import { useState, useEffect } from 'react';
import { Coffee, Cake, GlassWater, Loader2 } from 'lucide-react';
import { ENDPOINT } from '../utils/config';

interface Product {
  id: number;
  name: string;
  price: number;
  description: string;
  category: string;
  image_url: string;
  available: number;
}

const categoryIcons: Record<string, typeof Coffee> = {
  经典咖啡: Coffee,
  特调饮品: GlassWater,
  甜点: Cake,
};

const categoryColors: Record<
  string,
  { bg: string; text: string; border: string }
> = {
  经典咖啡: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
  },
  特调饮品: {
    bg: 'bg-teal-50',
    text: 'text-teal-700',
    border: 'border-teal-200',
  },
  甜点: { bg: 'bg-pink-50', text: 'text-pink-700', border: 'border-pink-200' },
};

export default function MenuPanel() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await fetch(`${ENDPOINT}/api/coffee/products`);
        const data = await response.json();
        if (data.success) {
          setProducts(data.data);
        }
      } catch (error) {
        console.error('Failed to fetch products:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const categories = [...new Set(products.map((p) => p.category))];

  const filteredProducts = selectedCategory
    ? products.filter((p) => p.category === selectedCategory)
    : products;

  const groupedProducts = filteredProducts.reduce((acc, product) => {
    if (!acc[product.category]) {
      acc[product.category] = [];
    }
    acc[product.category].push(product);
    return acc;
  }, {} as Record<string, Product[]>);

  if (loading) {
    return (
      <div className='flex items-center justify-center h-full'>
        <div className='text-center'>
          <Loader2 className='w-8 h-8 animate-spin text-coffee-500 mx-auto mb-2' />
          <p className='text-coffee-500'>加载菜单中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className='h-full flex flex-col'>
      {/* 分类筛选 */}
      <div className='p-4 border-b border-coffee-100'>
        <div className='flex space-x-2 overflow-x-auto pb-1'>
          <button
            onClick={() => setSelectedCategory(null)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              selectedCategory === null
                ? 'bg-coffee-600 text-white'
                : 'bg-coffee-100 text-coffee-600 hover:bg-coffee-200'
            }`}
          >
            全部
          </button>
          {categories.map((category) => {
            const Icon = categoryIcons[category] || Coffee;
            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`flex-shrink-0 flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  selectedCategory === category
                    ? 'bg-coffee-600 text-white'
                    : 'bg-coffee-100 text-coffee-600 hover:bg-coffee-200'
                }`}
              >
                <Icon className='w-4 h-4' />
                <span>{category}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 商品列表 */}
      <div className='flex-1 overflow-y-auto p-4'>
        {Object.entries(groupedProducts).map(([category, items]) => {
          const colors = categoryColors[category] || categoryColors['经典咖啡'];
          const Icon = categoryIcons[category] || Coffee;

          return (
            <div key={category} className='mb-6 last:mb-0'>
              {/* 分类标题 */}
              <div className='flex items-center space-x-2 mb-3'>
                <div className={`p-1.5 rounded-lg ${colors.bg}`}>
                  <Icon className={`w-4 h-4 ${colors.text}`} />
                </div>
                <h3 className='font-semibold text-coffee-800'>{category}</h3>
                <span className='text-xs text-coffee-400'>
                  ({items.length})
                </span>
              </div>

              {/* 商品网格 */}
              <div className='space-y-2'>
                {items.map((product) => (
                  <div
                    key={product.id}
                    className={`p-3 rounded-xl border ${colors.border} ${colors.bg} card-hover`}
                  >
                    <div className='flex items-start justify-between'>
                      <div className='flex items-start space-x-3'>
                        <span className='text-2xl'>{product.image_url}</span>
                        <div>
                          <h4 className='font-medium text-coffee-800'>
                            {product.name}
                          </h4>
                          <p className='text-sm text-coffee-500 mt-0.5'>
                            {product.description}
                          </p>
                        </div>
                      </div>
                      <div className='text-right'>
                        <p className='font-semibold text-coffee-700'>
                          ¥{product.price}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* 底部提示 */}
      <div className='p-4 border-t border-coffee-100 bg-gradient-to-r from-coffee-50 to-cream-100'>
        <div className='text-center'>
          <p className='text-sm text-coffee-600'>💡 通过左侧聊天助手下单</p>
          <p className='text-xs text-coffee-400 mt-1'>
            说 "我要一杯拿铁" 开始点单
          </p>
        </div>
      </div>
    </div>
  );
}
