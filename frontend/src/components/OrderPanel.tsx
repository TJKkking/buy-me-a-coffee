import { useState, useEffect } from 'react';
import {
  RefreshCw,
  Package,
  Clock,
  CheckCircle,
  Truck,
  XCircle,
  ChefHat,
  Loader2,
} from 'lucide-react';
import { ENDPOINT } from '../utils/config';

interface OrderItem {
  product_id: number;
  name: string;
  price: number;
  quantity: number;
}

interface Order {
  id: number;
  items: OrderItem[];
  total: number;
  status: string;
  customer_name: string;
  customer_phone: string;
  customer_address?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface Delivery {
  id: number;
  order_id: number;
  status: string;
  driver_name: string;
  driver_phone: string;
  delivery_address: string;
  estimated_time: number;
  created_at: string;
}

interface OrderPanelProps {
  onRefresh?: () => void;
}

const statusConfig: Record<
  string,
  { label: string; icon: typeof Package; color: string; bgColor: string }
> = {
  pending: {
    label: '待制作',
    icon: Clock,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
  },
  preparing: {
    label: '制作中',
    icon: ChefHat,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  ready: {
    label: '待取餐',
    icon: Package,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  delivering: {
    label: '配送中',
    icon: Truck,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
  },
  completed: {
    label: '已完成',
    icon: CheckCircle,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
  },
  cancelled: {
    label: '已取消',
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
  },
};

export default function OrderPanel({ onRefresh }: OrderPanelProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [deliveries, setDeliveries] = useState<Record<number, Delivery>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${ENDPOINT}/api/coffee/orders?limit=20`);
      const data = await response.json();
      if (data.success) {
        setOrders(data.data);
        // 获取配送信息
        for (const order of data.data) {
          if (order.customer_address) {
            try {
              const deliveryRes = await fetch(
                `${ENDPOINT}/api/delivery/deliveries/order/${order.id}`
              );
              const deliveryData = await deliveryRes.json();
              if (deliveryData.success) {
                setDeliveries((prev) => ({
                  ...prev,
                  [order.id]: deliveryData.data,
                }));
              }
            } catch {
              // 忽略配送查询错误
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchOrders();
    onRefresh?.();
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const isToday = date.toDateString() === today.toDateString();

    if (isToday) {
      return `今天 ${formatTime(dateStr)}`;
    }

    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-full'>
        <div className='text-center'>
          <Loader2 className='w-8 h-8 animate-spin text-coffee-500 mx-auto mb-2' />
          <p className='text-coffee-500'>加载订单中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className='h-full flex flex-col'>
      {/* 标题栏 */}
      <div className='p-4 border-b border-coffee-100 flex items-center justify-between'>
        <div>
          <h2 className='font-semibold text-coffee-800'>订单列表</h2>
          <p className='text-sm text-coffee-500'>共 {orders.length} 个订单</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className='p-2 rounded-lg hover:bg-coffee-100 text-coffee-600 transition-colors disabled:opacity-50'
        >
          <RefreshCw
            className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`}
          />
        </button>
      </div>

      {/* 订单列表 */}
      <div className='flex-1 overflow-y-auto p-4 space-y-3'>
        {orders.length === 0 ? (
          <div className='text-center py-12'>
            <Package className='w-12 h-12 text-coffee-300 mx-auto mb-3' />
            <p className='text-coffee-500'>暂无订单</p>
            <p className='text-sm text-coffee-400 mt-1'>通过聊天助手下单吧！</p>
          </div>
        ) : (
          orders.map((order) => {
            const status = statusConfig[order.status] || statusConfig.pending;
            const StatusIcon = status.icon;
            const delivery = deliveries[order.id];

            return (
              <div
                key={order.id}
                onClick={() =>
                  setSelectedOrder(
                    selectedOrder?.id === order.id ? null : order
                  )
                }
                className={`bg-white rounded-xl border transition-all cursor-pointer card-hover ${
                  selectedOrder?.id === order.id
                    ? 'border-coffee-400 shadow-md'
                    : 'border-coffee-100 hover:border-coffee-200'
                }`}
              >
                {/* 订单头部 */}
                <div className='p-3 flex items-center justify-between'>
                  <div className='flex items-center space-x-3'>
                    <div className={`p-2 rounded-lg ${status.bgColor}`}>
                      <StatusIcon className={`w-4 h-4 ${status.color}`} />
                    </div>
                    <div>
                      <div className='flex items-center space-x-2'>
                        <span className='font-medium text-coffee-800'>
                          #{order.id}
                        </span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${status.bgColor} ${status.color}`}
                        >
                          {status.label}
                        </span>
                      </div>
                      <p className='text-xs text-coffee-500'>
                        {formatDate(order.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className='text-right'>
                    <p className='font-semibold text-coffee-700'>
                      ¥{order.total.toFixed(2)}
                    </p>
                    <p className='text-xs text-coffee-500'>
                      {order.items.length} 件商品
                    </p>
                  </div>
                </div>

                {/* 展开详情 */}
                {selectedOrder?.id === order.id && (
                  <div className='px-3 pb-3 border-t border-coffee-50 pt-3 animate-fade-in'>
                    {/* 商品列表 */}
                    <div className='space-y-1 mb-3'>
                      {order.items.map((item, idx) => (
                        <div key={idx} className='flex justify-between text-sm'>
                          <span className='text-coffee-600'>
                            {item.name} x{item.quantity}
                          </span>
                          <span className='text-coffee-500'>
                            ¥{(item.price * item.quantity).toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* 客户信息 */}
                    <div className='text-sm space-y-1 pt-2 border-t border-coffee-50'>
                      <p className='text-coffee-600'>
                        <span className='text-coffee-400'>客户：</span>
                        {order.customer_name} ({order.customer_phone})
                      </p>
                      {order.customer_address && (
                        <p className='text-coffee-600'>
                          <span className='text-coffee-400'>地址：</span>
                          {order.customer_address}
                        </p>
                      )}
                      {order.notes && (
                        <p className='text-coffee-600'>
                          <span className='text-coffee-400'>备注：</span>
                          {order.notes}
                        </p>
                      )}
                    </div>

                    {/* 配送信息 */}
                    {delivery && (
                      <div className='mt-3 p-2 bg-purple-50 rounded-lg'>
                        <div className='flex items-center space-x-2 text-purple-700 text-sm'>
                          <Truck className='w-4 h-4' />
                          <span className='font-medium'>配送信息</span>
                        </div>
                        <div className='mt-1 text-sm text-purple-600 space-y-0.5'>
                          <p>
                            骑手：{delivery.driver_name} (
                            {delivery.driver_phone})
                          </p>
                          <p>预计 {delivery.estimated_time} 分钟送达</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 统计信息 */}
      <div className='p-4 border-t border-coffee-100 bg-coffee-50/50'>
        <div className='grid grid-cols-3 gap-2 text-center'>
          <div>
            <p className='text-lg font-semibold text-amber-600'>
              {orders.filter((o) => o.status === 'pending').length}
            </p>
            <p className='text-xs text-coffee-500'>待制作</p>
          </div>
          <div>
            <p className='text-lg font-semibold text-blue-600'>
              {orders.filter((o) => o.status === 'preparing').length}
            </p>
            <p className='text-xs text-coffee-500'>制作中</p>
          </div>
          <div>
            <p className='text-lg font-semibold text-green-600'>
              {
                orders.filter((o) => ['ready', 'completed'].includes(o.status))
                  .length
              }
            </p>
            <p className='text-xs text-coffee-500'>已完成</p>
          </div>
        </div>
      </div>
    </div>
  );
}
