#!/bin/bash

# PROJECT_ID=3514035
# PIPELINE_ID=38515
# eval $(cat .env | grep CI_TOKEN)

# if [ -z "$CI_TOKEN" ]; then
#   echo "Error: CI_TOKEN environment variable is not set."
#   exit 1
# fi



# IMAGE_AND_TAG=$(echo $IMAGE | awk -F/ '{print $3}')
# IMAGE_NAME=$(echo $IMAGE_AND_TAG | awk -F: '{print $1}')
# IMAGE_TAG=$(echo $IMAGE_AND_TAG | awk -F: '{print $2}')


# PAYLOAD=$(cat << EOF
# {
#   "branch": "master",
#   "params": {
#     "baseImage": "$IMAGE",
#     "targetImageName": "${IMAGE_NAME}",
#     "targetImageTag": "${IMAGE_TAG}",
#     "mainland-regions": [ "cn-beijing", "cn-shanghai", "cn-shenzhen", "cn-hangzhou" ],
#     "international-regions": [ "ap-southeast-1" ]
#   }
# }
# EOF
# )

# RESP=$(curl "https://aone-ci-core.alibaba-inc.com/openapi/v1/projects/${PROJECT_ID}/pipelines/${PIPELINE_ID}/run?private_token=${CI_TOKEN}" -s \
#     -XPOST \
#     -H "Content-Type: application/json" \
#     -d "$PAYLOAD")

# echo $RESP

# # waiting for ready
# RUN_ID=$(echo $RESP | sed -n 's/.*"id":\([0-9]*\).*/\1/p')
# echo "RunID: $RUN_ID"


# while true; do
#     STATUS=$(curl "https://aone-ci-core.alibaba-inc.com/openapi/v1/projects/${PROJECT_ID}/runs/${RUN_ID}?private_token=${CI_TOKEN}" -s | grep -o -E '"isFinished":(true|false)' | awk -F: '{print $2}')
#     echo "Pipeline status: $STATUS"
#     if [ "$STATUS" == "true" ]; then
#         break
#     fi
#     if [ "$STATUS" != "false" ]; then
#         echo "failed to get pipeline status"
#         exit 1
#     fi

#     echo "waiting for prewarm pipeline to finish..."
#     sleep 5
# done


REGIONS="cn-beijing cn-shanghai cn-shenzhen cn-hangzhou ap-southeast-1 us-west-1"
FAILED_FILE="temp/prewarm-failed"
NAME=prewarm-image-$(echo $IMAGE | md5sum | awk '{print $1}')

function doRegion() {
    REGION=$1

    FILE=temp/s-${REGION}-${NAME}.yaml
    LOG=temp/s-${REGION}-${NAME}.log

    mkdir -p temp

    cat << EOF > ${FILE}
edition: 3.0.0
name: acc
vars:
  name: "${NAME}"
  region: "${REGION}"
  image: "${IMAGE}"

resources:
  acc-func:
    component: fc3
    props:
      functionName: acc-image-\${vars.name}
      description:  "共享镜像加速预热 \${vars.image}"
      region: \${vars.region}
      role: "acs:ram::1431999136518149:role/aliyunfcdefaultrole"
      handler: index.handler
      timeout: 7200
      diskSize: 512
      caPort: 9000
      runtime: custom-container
      codeUri: ./dist
      customContainerConfig:
        image: \${vars.image}
        registryConfig:
            certConfig:
                insecure: false
      instanceConcurrency: 100
      cpu: 8
      memorySize: 16384
      # gpuConfig:
      #   gpuMemorySize: 16384
      #   gpuType: fc.gpu.tesla.1
EOF

  echo "deploy to $REGION, ${NAME}"

  s remove -t "${FILE}" -y -a quanxi-fc >> "${LOG}" 
  s deploy -y --skip-push -t "${FILE}" -a quanxi-fc >> "${LOG}" 

  if [ $? -eq 0 ]; then
    echo -e "\033[1;32m[SUCC]\033[0m deploy to $REGION done, https://fcnext.console.aliyun.com/${REGION}/functions/${NAME}?tab=detail&section=code"
  else
    echo -e "\033[1;31m[ERRO]\033[0m deploy to $REGION failed"
    cat "${LOG}"
    echo "failed" > "${FAILED_FILE}"
  fi

  s remove -t "${FILE}" -y -a quanxi-fc >> "${LOG}" 
}

export -f doRegion
export TAG
export FAILED_FILE
export NAME

rm -f "${FAILED_FILE}"
echo "${REGIONS}" | sed 's/ /\n/g' | xargs -P8 -I {} bash -c 'doRegion "{}"'

echo "${FAILED_FILE}"
if [ -e "${FAILED_FILE}" ]; then
    echo "prewarm failed"
    exit 1
fi

