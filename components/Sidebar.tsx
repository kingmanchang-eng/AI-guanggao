'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const nav = [
  { href: '/', label: '概览', icon: '📊' },
  { href: '/websites', label: '网站管理', icon: '🌐' },
  { href: '/accounts', label: '广告账号', icon: '📋' },
  { href: '/campaigns', label: '创建广告', icon: '✨' },
  { href: '/logs', label: '操作日志', icon: '📝' },
  { href: '/safety', label: '异常中心', icon: '🛡️' },
]

export default function Sidebar() {
  const path = usePathname()
  return (
    <aside className="w-56 min-h-screen bg-gray-900 text-white flex flex-col">
      <div className="px-6 py-5 border-b border-gray-700">
        <h1 className="text-sm font-bold text-white leading-tight">AI Google Ads</h1>
        <p className="text-xs text-gray-400 mt-0.5">全托管投放系统</p>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(item => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              path === item.href
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="px-6 py-4 border-t border-gray-700">
        <p className="text-xs text-gray-500">后端：usw-1.sealos.app</p>
      </div>
    </aside>
  )
}
