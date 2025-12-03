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
  Coffee,
  MapPin,
  Phone,
  User,
  ChevronDown,
  ChevronUp,
  Bike,
  Navigation,
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
  customer_name: string;
  customer_phone: string;
  estimated_time: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface AdminPanelProps {
  refreshTrigger: number;
  onRefresh?: () => void;
}

// 咖啡订单状态配置
const coffeeStatusConfig: Record<
  string,
  {
    label: string;
    icon: typeof Package;
    color: string;
    bgColor: string;
    borderColor: string;
  }
> = {
  pending: {
    label: '待制作',
    icon: Clock,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
  },
  preparing: {
    label: '制作中',
    icon: ChefHat,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  ready: {
    label: '制作完成',
    icon: Package,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
  completed: {
    label: '已领取',
    icon: CheckCircle,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
  },
  cancelled: {
    label: '已取消',
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
  },
};

// 配送状态配置
const deliveryStatusConfig: Record<
  string,
  {
    label: string;
    icon: typeof Truck;
    color: string;
    bgColor: string;
    borderColor: string;
  }
> = {
  pending: {
    label: '待分配',
    icon: Clock,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
  },
  assigned: {
    label: '已分配',
    icon: Bike,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  picked: {
    label: '已取货',
    icon: Package,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
  },
  delivering: {
    label: '配送中',
    icon: Navigation,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
  },
  delivered: {
    label: '已送达',
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
  cancelled: {
    label: '已取消',
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
  },
};

// 咖啡订单状态流转
const coffeeStatusFlow = ['pending', 'preparing', 'ready', 'completed'];
// 配送状态流转
const deliveryStatusFlow = [
  'pending',
  'assigned',
  'picked',
  'delivering',
  'delivered',
];

export default function AdminPanel({
  refreshTrigger,
  onRefresh,
}: AdminPanelProps) {
  const [activeTab, setActiveTab] = useState<'coffee' | 'delivery'>('coffee');
  const [orders, setOrders] = useState<Order[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedOrderId, setExpandedOrderId] = useState<number | null>(null);
  const [expandedDeliveryId, setExpandedDeliveryId] = useState<number | null>(
    null
  );
  const [updatingStatus, setUpdatingStatus] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      // 获取咖啡订单
      const ordersRes = await fetch(`${ENDPOINT}/api/coffee/orders?limit=50`);
      const ordersData = await ordersRes.json();
      if (ordersData.success) {
        setOrders(ordersData.data);
      }

      // 获取配送订单
      const deliveriesRes = await fetch(
        `${ENDPOINT}/api/delivery/deliveries?limit=50`
      );
      const deliveriesData = await deliveriesRes.json();
      if (deliveriesData.success) {
        setDeliveries(deliveriesData.data);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshTrigger]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
    onRefresh?.();
  };

  // 更新咖啡订单状态
  const updateOrderStatus = async (orderId: number, newStatus: string) => {
    setUpdatingStatus(orderId);
    try {
      const response = await fetch(
        `${ENDPOINT}/api/coffee/orders/${orderId}/status`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus }),
        }
      );
      const data = await response.json();
      if (data.success) {
        setOrders((prev) =>
          prev.map((order) =>
            order.id === orderId ? { ...order, status: newStatus } : order
          )
        );
      }
    } catch (error) {
      console.error('Failed to update order status:', error);
    } finally {
      setUpdatingStatus(null);
    }
  };

  // 更新配送状态
  const updateDeliveryStatus = async (
    deliveryId: number,
    newStatus: string
  ) => {
    setUpdatingStatus(deliveryId);
    try {
      const response = await fetch(
        `${ENDPOINT}/api/delivery/deliveries/${deliveryId}/status`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus }),
        }
      );
      const data = await response.json();
      if (data.success) {
        setDeliveries((prev) =>
          prev.map((delivery) =>
            delivery.id === deliveryId
              ? { ...delivery, status: newStatus }
              : delivery
          )
        );
      }
    } catch (error) {
      console.error('Failed to update delivery status:', error);
    } finally {
      setUpdatingStatus(null);
    }
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      });
    }
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 获取下一个状态
  const getNextStatus = (currentStatus: string, statusFlow: string[]) => {
    const currentIndex = statusFlow.indexOf(currentStatus);
    if (currentIndex === -1 || currentIndex === statusFlow.length - 1)
      return null;
    return statusFlow[currentIndex + 1];
  };

  if (loading) {
    return (
      <div className='h-full flex items-center justify-center bg-slate-50'>
        <div className='text-center'>
          <Loader2 className='w-10 h-10 animate-spin text-slate-400 mx-auto mb-3' />
          <p className='text-slate-500'>加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className='h-full flex flex-col bg-slate-50'>
      {/* 顶部标题 */}
      <div className='bg-gradient-to-r from-slate-800 to-slate-700 text-white px-6 py-4'>
        <div className='flex items-center justify-between'>
          <div>
            <h1 className='text-xl font-bold'>商家后台</h1>
            <p className='text-slate-300 text-sm'>订单管理系统</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className='p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50'
          >
            <RefreshCw
              className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Tab 切换 */}
      <div className='bg-white border-b border-slate-200 px-4'>
        <div className='flex'>
          <button
            onClick={() => setActiveTab('coffee')}
            className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'coffee'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Coffee className='w-4 h-4' />
            咖啡订单
            <span
              className={`px-2 py-0.5 rounded-full text-xs ${
                activeTab === 'coffee'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {orders.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('delivery')}
            className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'delivery'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Truck className='w-4 h-4' />
            配送订单
            <span
              className={`px-2 py-0.5 rounded-full text-xs ${
                activeTab === 'delivery'
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {deliveries.length}
            </span>
          </button>
        </div>
      </div>

      {/* 订单列表 */}
      <div className='flex-1 overflow-y-auto p-4'>
        {activeTab === 'coffee' ? (
          // 咖啡订单列表
          <div className='space-y-3'>
            {orders.length === 0 ? (
              <div className='text-center py-16'>
                <Coffee className='w-16 h-16 text-slate-300 mx-auto mb-4' />
                <p className='text-slate-500 text-lg'>暂无咖啡订单</p>
                <p className='text-slate-400 text-sm mt-1'>等待顾客下单...</p>
              </div>
            ) : (
              orders.map((order) => {
                const status =
                  coffeeStatusConfig[order.status] ||
                  coffeeStatusConfig.pending;
                const StatusIcon = status.icon;
                const isExpanded = expandedOrderId === order.id;
                const nextStatus = getNextStatus(
                  order.status,
                  coffeeStatusFlow
                );
                const nextStatusConfig = nextStatus
                  ? coffeeStatusConfig[nextStatus]
                  : null;

                return (
                  <div
                    key={order.id}
                    className={`bg-white rounded-xl border-2 transition-all overflow-hidden ${
                      status.borderColor
                    } ${
                      isExpanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'
                    }`}
                  >
                    {/* 订单头部 */}
                    <div
                      className='p-4 cursor-pointer'
                      onClick={() =>
                        setExpandedOrderId(isExpanded ? null : order.id)
                      }
                    >
                      <div className='flex items-center justify-between'>
                        <div className='flex items-center gap-3'>
                          <div className={`p-2.5 rounded-xl ${status.bgColor}`}>
                            <StatusIcon className={`w-5 h-5 ${status.color}`} />
                          </div>
                          <div>
                            <div className='flex items-center gap-2'>
                              <span className='font-bold text-slate-800 text-lg'>
                                #{order.id}
                              </span>
                              <span
                                className={`text-xs px-2.5 py-1 rounded-full font-medium ${status.bgColor} ${status.color}`}
                              >
                                {status.label}
                              </span>
                            </div>
                            <p className='text-sm text-slate-500 mt-0.5'>
                              {formatTime(order.created_at)}
                            </p>
                          </div>
                        </div>
                        <div className='flex items-center gap-4'>
                          <div className='text-right'>
                            <p className='font-bold text-slate-800 text-lg'>
                              ¥{order.total.toFixed(2)}
                            </p>
                            <p className='text-xs text-slate-500'>
                              {order.items.length} 件商品
                            </p>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className='w-5 h-5 text-slate-400' />
                          ) : (
                            <ChevronDown className='w-5 h-5 text-slate-400' />
                          )}
                        </div>
                      </div>
                    </div>

                    {/* 展开详情 */}
                    {isExpanded && (
                      <div className='px-4 pb-4 border-t border-slate-100 animate-fade-in'>
                        {/* 商品列表 */}
                        <div className='mt-4 space-y-2'>
                          <h4 className='text-sm font-medium text-slate-700'>
                            商品明细
                          </h4>
                          {order.items.map((item, idx) => (
                            <div
                              key={idx}
                              className='flex justify-between text-sm py-1.5 px-3 bg-slate-50 rounded-lg'
                            >
                              <span className='text-slate-700'>
                                {item.name} × {item.quantity}
                              </span>
                              <span className='text-slate-500 font-medium'>
                                ¥{(item.price * item.quantity).toFixed(2)}
                              </span>
                            </div>
                          ))}
                        </div>

                        {/* 客户信息 */}
                        <div className='mt-4 p-3 bg-slate-50 rounded-lg space-y-2'>
                          <h4 className='text-sm font-medium text-slate-700'>
                            客户信息
                          </h4>
                          <div className='flex items-center gap-2 text-sm text-slate-600'>
                            <User className='w-4 h-4 text-slate-400' />
                            <span>{order.customer_name}</span>
                          </div>
                          <div className='flex items-center gap-2 text-sm text-slate-600'>
                            <Phone className='w-4 h-4 text-slate-400' />
                            <span>{order.customer_phone}</span>
                          </div>
                          {order.customer_address && (
                            <div className='flex items-center gap-2 text-sm text-slate-600'>
                              <MapPin className='w-4 h-4 text-slate-400' />
                              <span>{order.customer_address}</span>
                            </div>
                          )}
                          {order.notes && (
                            <div className='text-sm text-amber-600 bg-amber-50 px-2 py-1 rounded mt-2'>
                              📝 备注: {order.notes}
                            </div>
                          )}
                        </div>

                        {/* 状态操作 */}
                        {nextStatusConfig && order.status !== 'cancelled' && (
                          <div className='mt-4'>
                            <button
                              onClick={() =>
                                updateOrderStatus(order.id, nextStatus!)
                              }
                              disabled={updatingStatus === order.id}
                              className={`w-full py-3 rounded-xl font-medium text-white transition-all flex items-center justify-center gap-2 ${
                                nextStatus === 'preparing'
                                  ? 'bg-blue-500 hover:bg-blue-600'
                                  : nextStatus === 'ready'
                                  ? 'bg-green-500 hover:bg-green-600'
                                  : nextStatus === 'completed'
                                  ? 'bg-slate-500 hover:bg-slate-600'
                                  : 'bg-slate-500 hover:bg-slate-600'
                              } disabled:opacity-50`}
                            >
                              {updatingStatus === order.id ? (
                                <Loader2 className='w-4 h-4 animate-spin' />
                              ) : (
                                <>
                                  <nextStatusConfig.icon className='w-4 h-4' />
                                  标记为: {nextStatusConfig.label}
                                </>
                              )}
                            </button>
                          </div>
                        )}

                        {/* 取消订单 */}
                        {order.status !== 'completed' &&
                          order.status !== 'cancelled' && (
                            <button
                              onClick={() =>
                                updateOrderStatus(order.id, 'cancelled')
                              }
                              disabled={updatingStatus === order.id}
                              className='w-full mt-2 py-2 rounded-xl font-medium text-red-600 border border-red-200 hover:bg-red-50 transition-all'
                            >
                              取消订单
                            </button>
                          )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        ) : (
          // 配送订单列表
          <div className='space-y-3'>
            {deliveries.length === 0 ? (
              <div className='text-center py-16'>
                <Truck className='w-16 h-16 text-slate-300 mx-auto mb-4' />
                <p className='text-slate-500 text-lg'>暂无配送订单</p>
                <p className='text-slate-400 text-sm mt-1'>等待配送请求...</p>
              </div>
            ) : (
              deliveries.map((delivery) => {
                const status =
                  deliveryStatusConfig[delivery.status] ||
                  deliveryStatusConfig.pending;
                const StatusIcon = status.icon;
                const isExpanded = expandedDeliveryId === delivery.id;
                const nextStatus = getNextStatus(
                  delivery.status,
                  deliveryStatusFlow
                );
                const nextStatusConfig = nextStatus
                  ? deliveryStatusConfig[nextStatus]
                  : null;

                return (
                  <div
                    key={delivery.id}
                    className={`bg-white rounded-xl border-2 transition-all overflow-hidden ${
                      status.borderColor
                    } ${
                      isExpanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'
                    }`}
                  >
                    {/* 配送头部 */}
                    <div
                      className='p-4 cursor-pointer'
                      onClick={() =>
                        setExpandedDeliveryId(isExpanded ? null : delivery.id)
                      }
                    >
                      <div className='flex items-center justify-between'>
                        <div className='flex items-center gap-3'>
                          <div className={`p-2.5 rounded-xl ${status.bgColor}`}>
                            <StatusIcon className={`w-5 h-5 ${status.color}`} />
                          </div>
                          <div>
                            <div className='flex items-center gap-2'>
                              <span className='font-bold text-slate-800 text-lg'>
                                配送 #{delivery.id}
                              </span>
                              <span
                                className={`text-xs px-2.5 py-1 rounded-full font-medium ${status.bgColor} ${status.color}`}
                              >
                                {status.label}
                              </span>
                            </div>
                            <p className='text-sm text-slate-500 mt-0.5'>
                              关联订单 #{delivery.order_id}
                            </p>
                          </div>
                        </div>
                        <div className='flex items-center gap-4'>
                          <div className='text-right'>
                            <p className='text-sm text-slate-600'>
                              预计 {delivery.estimated_time} 分钟
                            </p>
                            <p className='text-xs text-slate-500'>
                              {formatTime(delivery.created_at)}
                            </p>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className='w-5 h-5 text-slate-400' />
                          ) : (
                            <ChevronDown className='w-5 h-5 text-slate-400' />
                          )}
                        </div>
                      </div>
                    </div>

                    {/* 展开详情 */}
                    {isExpanded && (
                      <div className='px-4 pb-4 border-t border-slate-100 animate-fade-in'>
                        {/* 骑手信息 */}
                        <div className='mt-4 p-3 bg-purple-50 rounded-lg space-y-2'>
                          <h4 className='text-sm font-medium text-purple-700 flex items-center gap-2'>
                            <Bike className='w-4 h-4' />
                            骑手信息
                          </h4>
                          <div className='flex items-center gap-2 text-sm text-purple-600'>
                            <User className='w-4 h-4 text-purple-400' />
                            <span>{delivery.driver_name}</span>
                          </div>
                          <div className='flex items-center gap-2 text-sm text-purple-600'>
                            <Phone className='w-4 h-4 text-purple-400' />
                            <span>{delivery.driver_phone}</span>
                          </div>
                        </div>

                        {/* 配送信息 */}
                        <div className='mt-3 p-3 bg-slate-50 rounded-lg space-y-2'>
                          <h4 className='text-sm font-medium text-slate-700'>
                            配送信息
                          </h4>
                          <div className='flex items-center gap-2 text-sm text-slate-600'>
                            <User className='w-4 h-4 text-slate-400' />
                            <span>收货人: {delivery.customer_name}</span>
                          </div>
                          <div className='flex items-center gap-2 text-sm text-slate-600'>
                            <Phone className='w-4 h-4 text-slate-400' />
                            <span>{delivery.customer_phone}</span>
                          </div>
                          <div className='flex items-start gap-2 text-sm text-slate-600'>
                            <MapPin className='w-4 h-4 text-slate-400 mt-0.5' />
                            <span>{delivery.delivery_address}</span>
                          </div>
                          {delivery.notes && (
                            <div className='text-sm text-amber-600 bg-amber-50 px-2 py-1 rounded mt-2'>
                              📝 备注: {delivery.notes}
                            </div>
                          )}
                        </div>

                        {/* 状态操作 */}
                        {nextStatusConfig &&
                          delivery.status !== 'cancelled' && (
                            <div className='mt-4'>
                              <button
                                onClick={() =>
                                  updateDeliveryStatus(delivery.id, nextStatus!)
                                }
                                disabled={updatingStatus === delivery.id}
                                className={`w-full py-3 rounded-xl font-medium text-white transition-all flex items-center justify-center gap-2 ${
                                  nextStatus === 'assigned'
                                    ? 'bg-blue-500 hover:bg-blue-600'
                                    : nextStatus === 'picked'
                                    ? 'bg-indigo-500 hover:bg-indigo-600'
                                    : nextStatus === 'delivering'
                                    ? 'bg-purple-500 hover:bg-purple-600'
                                    : nextStatus === 'delivered'
                                    ? 'bg-green-500 hover:bg-green-600'
                                    : 'bg-slate-500 hover:bg-slate-600'
                                } disabled:opacity-50`}
                              >
                                {updatingStatus === delivery.id ? (
                                  <Loader2 className='w-4 h-4 animate-spin' />
                                ) : (
                                  <>
                                    <nextStatusConfig.icon className='w-4 h-4' />
                                    标记为: {nextStatusConfig.label}
                                  </>
                                )}
                              </button>
                            </div>
                          )}

                        {/* 取消配送 */}
                        {delivery.status !== 'delivered' &&
                          delivery.status !== 'cancelled' && (
                            <button
                              onClick={() =>
                                updateDeliveryStatus(delivery.id, 'cancelled')
                              }
                              disabled={updatingStatus === delivery.id}
                              className='w-full mt-2 py-2 rounded-xl font-medium text-red-600 border border-red-200 hover:bg-red-50 transition-all'
                            >
                              取消配送
                            </button>
                          )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* 底部统计 */}
      <div className='bg-white border-t border-slate-200 px-4 py-3'>
        {activeTab === 'coffee' ? (
          <div className='grid grid-cols-4 gap-2 text-center'>
            <div className='p-2 rounded-lg bg-amber-50'>
              <p className='text-xl font-bold text-amber-600'>
                {orders.filter((o) => o.status === 'pending').length}
              </p>
              <p className='text-xs text-amber-700'>待制作</p>
            </div>
            <div className='p-2 rounded-lg bg-blue-50'>
              <p className='text-xl font-bold text-blue-600'>
                {orders.filter((o) => o.status === 'preparing').length}
              </p>
              <p className='text-xs text-blue-700'>制作中</p>
            </div>
            <div className='p-2 rounded-lg bg-green-50'>
              <p className='text-xl font-bold text-green-600'>
                {orders.filter((o) => o.status === 'ready').length}
              </p>
              <p className='text-xs text-green-700'>待取餐</p>
            </div>
            <div className='p-2 rounded-lg bg-slate-100'>
              <p className='text-xl font-bold text-slate-600'>
                {orders.filter((o) => o.status === 'completed').length}
              </p>
              <p className='text-xs text-slate-600'>已完成</p>
            </div>
          </div>
        ) : (
          <div className='grid grid-cols-5 gap-2 text-center'>
            <div className='p-2 rounded-lg bg-amber-50'>
              <p className='text-lg font-bold text-amber-600'>
                {deliveries.filter((d) => d.status === 'pending').length}
              </p>
              <p className='text-[10px] text-amber-700'>待分配</p>
            </div>
            <div className='p-2 rounded-lg bg-blue-50'>
              <p className='text-lg font-bold text-blue-600'>
                {deliveries.filter((d) => d.status === 'assigned').length}
              </p>
              <p className='text-[10px] text-blue-700'>已分配</p>
            </div>
            <div className='p-2 rounded-lg bg-indigo-50'>
              <p className='text-lg font-bold text-indigo-600'>
                {deliveries.filter((d) => d.status === 'picked').length}
              </p>
              <p className='text-[10px] text-indigo-700'>已取货</p>
            </div>
            <div className='p-2 rounded-lg bg-purple-50'>
              <p className='text-lg font-bold text-purple-600'>
                {deliveries.filter((d) => d.status === 'delivering').length}
              </p>
              <p className='text-[10px] text-purple-700'>配送中</p>
            </div>
            <div className='p-2 rounded-lg bg-green-50'>
              <p className='text-lg font-bold text-green-600'>
                {deliveries.filter((d) => d.status === 'delivered').length}
              </p>
              <p className='text-[10px] text-green-700'>已送达</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
