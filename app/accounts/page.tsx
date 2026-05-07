'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { api } from '@/lib/api'

export default function AccountsPage() {
  const { data: managers } = useSWR('managers', api.listManagers)
  const { data: adsAccounts } = useSWR('ads', api.listAdsAccounts)
  const { data: bindings, mutate: mutateBindings } = useSWR('bindings', api.listBindings)
  const { data: websites } = useSWR('websites', api.listWebsites)
  const [tab, setTab] = useState<'managers' | 'ads' | 'bindings'>('bindings')
  const [msg, setMsg] = useState('')

  async function handleToggleAutopilot(bindingId: string, current: boolean) {
    try {
      await api.toggleAutopilot(bindingId, !current)
      mutateBindings()
      setMsg(`✅ AI 全托管已${!current ? '开启' : '关闭'}`)
    } catch (err: any) {
      setMsg(`❌ ${err.message}`)
    }
  }

  async function handleOptimize(websiteId: string) {
    try {
      await api.triggerOptimize(websiteId)
      setMsg('✅ AI 优化任务已触发，请稍后查看操作日志')
    } catch (err: any) {
      setMsg(`❌ ${err.message}`)
    }
  }

  const tabs = [
    { key: 'bindings', label: '网站绑定' },
    { key: 'managers', label: 'MCC 账号' },
    { key: 'ads', label: '广告客户账号' },
  ]

  return (
    <div className="p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">广告账号管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理 MCC 授权、广告账号和网站绑定关系</p>
      </div>

      {msg && (
        <div className="mb-4 px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm">{msg}</div>
      )}

      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key as any)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Bindings tab */}
      {tab === 'bindings' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">网站与广告账号绑定（{bindings?.length ?? 0}）</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {!bindings && <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>}
            {bindings?.length === 0 && (
              <p className="px-6 py-8 text-center text-gray-400 text-sm">
                暂无绑定。请先在网站管理页添加网站，然后在后端 API 创建绑定关系。
              </p>
            )}
            {bindings?.map((b: any) => (
              <div key={b.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{b.websites?.domain ?? b.website_id}</p>
                    <p className="text-sm text-gray-500 mt-0.5">
                      customer_id: <span className="font-mono">{b.customer_id}</span>
                      {b.ads_accounts?.account_name && ` · ${b.ads_accounts.account_name}`}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      预算上限: {b.daily_budget_cap ? `$${b.daily_budget_cap}/天` : '未设置'} ·
                      每日最多 {b.max_actions_per_day} 条操作
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {b.safety_paused && (
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">🛡️ 安全暂停</span>
                    )}
                    <button
                      onClick={() => handleOptimize(b.website_id)}
                      className="px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      触发优化
                    </button>
                    <button
                      onClick={() => handleToggleAutopilot(b.id, b.ai_autopilot_enabled)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        b.ai_autopilot_enabled ? 'bg-green-500' : 'bg-gray-300'
                      }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        b.ai_autopilot_enabled ? 'translate-x-6' : 'translate-x-1'
                      }`} />
                    </button>
                    <span className="text-xs text-gray-500 w-16">
                      {b.ai_autopilot_enabled ? 'AI 托管中' : '已关闭'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Managers tab */}
      {tab === 'managers' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">MCC 经理账号（{managers?.length ?? 0}）</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {!managers && <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>}
            {managers?.length === 0 && (
              <p className="px-6 py-8 text-center text-gray-400 text-sm">
                暂无 MCC 账号。Google Ads API 配置完成后将自动同步。
              </p>
            )}
            {managers?.map((m: any) => (
              <div key={m.id} className="px-6 py-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{m.manager_name ?? '未命名'}</p>
                  <p className="text-sm text-gray-500 mt-0.5">
                    login_customer_id: <span className="font-mono">{m.login_customer_id}</span>
                  </p>
                  {m.oauth_user_email && (
                    <p className="text-xs text-gray-400 mt-0.5">{m.oauth_user_email}</p>
                  )}
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  m.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {m.status === 'active' ? '已授权' : m.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ads accounts tab */}
      {tab === 'ads' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">广告客户账号（{adsAccounts?.length ?? 0}）</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {!adsAccounts && <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>}
            {adsAccounts?.length === 0 && (
              <p className="px-6 py-8 text-center text-gray-400 text-sm">
                暂无广告账号。Google Ads API 配置完成后将自动同步。
              </p>
            )}
            {adsAccounts?.map((a: any) => (
              <div key={a.id} className="px-6 py-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{a.account_name ?? '未命名'}</p>
                  <p className="text-sm text-gray-500 mt-0.5">
                    customer_id: <span className="font-mono">{a.customer_id}</span>
                    {a.currency_code && ` · ${a.currency_code}`}
                    {a.time_zone && ` · ${a.time_zone}`}
                  </p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  a.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {a.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
