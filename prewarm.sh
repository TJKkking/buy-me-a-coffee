#!/bin/bash


REGIONS="cn-beijing cn-shanghai cn-shenzhen cn-hangzhou ap-southeast-1"
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
      gpuConfig:
        gpuMemorySize: 16384
        gpuType: fc.gpu.tesla.1
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

