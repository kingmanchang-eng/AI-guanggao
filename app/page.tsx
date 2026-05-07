'use client'
import useSWR from 'swr'
import { api } from '@/lib/api'

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
    </div>
  )
}

export default function Dashboard() {
  const { data: health } = useSWR('health', api.health, { refreshInterval: 30000 })
  const { data: websites } = useSWR('websites', api.listWebsites)
  const { data: bindings } = useSWR('bindings', api.listBindings)
  const { data: managers } = useSWR('managers', api.listManagers)

  const activeBindings = bindings?.filter((b: any) => b.ai_autopilot_enabled) ?? []
  const pausedBindings = bindings?.filter((b: any) => b.safety_paused) ?? []

  return (
    <div className="p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">系统概览</h2>
        <p className="text-sm text-gray-500 mt-1">AI Google Ads 全托管自动投放平台</p>
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-2 mb-6 bg-white rounded-lg px-4 py-3 shadow-sm border border-gray-100">
        <span className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-sm text-gray-600">
          后端状态：{health?.status === 'ok' ? '正常运行' : '连接异常'}
        </span>
        <span className="mx-2 text-gray-300">|</span>
        <span className={`w-2 h-2 rounded-full ${health?.db === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-sm text-gray-600">
          数据库：{health?.db === 'connected' ? '已连接' : '未连接'}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="网站总数" value={String(websites?.length ?? '-')} color="text-blue-600" />
        <StatCard label="MCC 账号" value={String(managers?.length ?? '-')} color="text-purple-600" />
        <StatCard label="AI 全托管中" value={String(activeBindings.length)} color="text-green-600" />
        <StatCard label="安全暂停" value={String(pausedBindings.length)} color="text-red-600" />
      </div>

      {/* Website list */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-6 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">网站与广告账号绑定状态</h3>
        </div>
        <div className="divide-y divide-gray-50">
          {!bindings && (
            <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>
          )}
          {bindings?.length === 0 && (
            <p className="px-6 py-8 text-center text-gray-400 text-sm">暂无绑定，请先添加网站和广告账号</p>
          )}
          {bindings?.map((b: any) => (
            <div key={b.id} className="px-6 py-4 flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{b.websites?.domain ?? b.website_id}</p>
                <p className="text-sm text-gray-500 mt-0.5">
                  customer_id: {b.customer_id} · {b.ads_accounts?.account_name ?? ''}
                </p>
              </div>
              <div className="flex items-center gap-3">
                {b.safety_paused && (
                  <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">安全暂停</span>
                )}
                <span className={`px-2 py-1 text-xs rounded-full ${
                  b.ai_autopilot_enabled
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  {b.ai_autopilot_enabled ? 'AI 全托管' : '已关闭'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
