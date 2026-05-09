'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { api } from '@/lib/api'

export default function AccountsPage() {
  const { data: managers, mutate: mutateManagers } = useSWR('managers', api.listManagers)
  const { data: adsAccounts, mutate: mutateAds } = useSWR('ads', api.listAdsAccounts)
  const { data: bindings, mutate: mutateBindings } = useSWR('bindings', api.listBindings)
  const { data: websites } = useSWR('websites', api.listWebsites)
  const [tab, setTab] = useState<'bindings' | 'managers' | 'ads'>('bindings')
  const [msg, setMsg] = useState('')

  // 绑定表单
  const [showBindForm, setShowBindForm] = useState(false)
  const [bindForm, setBindForm] = useState({
    website_id: '', manager_account_id: '', ads_account_id: '',
    customer_id: '', daily_budget_cap: '',
  })

  // MCC 表单
  const [showMccForm, setShowMccForm] = useState(false)
  const [mccForm, setMccForm] = useState({ login_customer_id: '', manager_name: '', oauth_user_email: '' })

  // 广告账号表单
  const [showAdsForm, setShowAdsForm] = useState(false)
  const [adsForm, setAdsForm] = useState({ manager_account_id: '', customer_id: '', account_name: '', currency_code: 'USD', time_zone: 'Asia/Shanghai' })

  const [saving, setSaving] = useState(false)

  const setError = (err: any) => setMsg(`❌ ${err.message || err}`)

  async function handleCreateBinding(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true); setMsg('')
    try {
      await api.createBinding({
        ...bindForm,
        daily_budget_cap: bindForm.daily_budget_cap ? parseFloat(bindForm.daily_budget_cap) : null,
      })
      setMsg('✅ 绑定创建成功')
      setShowBindForm(false)
      setBindForm({ website_id: '', manager_account_id: '', ads_account_id: '', customer_id: '', daily_budget_cap: '' })
      mutateBindings()
    } catch (err: any) { setError(err) } finally { setSaving(false) }
  }

  async function handleCreateManager(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true); setMsg('')
    try {
      await api.createManager(mccForm)
      setMsg('✅ MCC 账号添加成功')
      setShowMccForm(false)
      setMccForm({ login_customer_id: '', manager_name: '', oauth_user_email: '' })
      mutateManagers()
    } catch (err: any) { setError(err) } finally { setSaving(false) }
  }

  async function handleCreateAdsAccount(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true); setMsg('')
    try {
      await api.createAdsAccount(adsForm)
      setMsg('✅ 广告账号添加成功')
      setShowAdsForm(false)
      setAdsForm({ manager_account_id: '', customer_id: '', account_name: '', currency_code: 'USD', time_zone: 'Asia/Shanghai' })
      mutateAds()
    } catch (err: any) { setError(err) } finally { setSaving(false) }
  }

  async function handleToggleAutopilot(bindingId: string, current: boolean) {
    try {
      await api.toggleAutopilot(bindingId, !current)
      mutateBindings()
      setMsg(`✅ AI 全托管已${!current ? '开启' : '关闭'}`)
    } catch (err: any) { setError(err) }
  }

  async function handleOptimize(websiteId: string) {
    try {
      await api.triggerOptimize(websiteId)
      setMsg('✅ AI 优化任务已触发，请稍后查看操作日志')
    } catch (err: any) { setError(err) }
  }

  async function handleSync(websiteId: string) {
    try {
      await api.triggerSync(websiteId)
      setMsg('✅ 数据同步任务已触发')
    } catch (err: any) { setError(err) }
  }

  const inputCls = 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
  const labelCls = 'block text-sm text-gray-600 mb-1'

  return (
    <div className="p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">广告账号管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理 MCC 授权、广告账号和网站绑定关系</p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm border ${msg.startsWith('✅') ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
          {msg}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[['bindings', '网站绑定'], ['managers', 'MCC 账号'], ['ads', '广告客户账号']].map(([k, label]) => (
          <button key={k} onClick={() => setTab(k as any)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === k ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── 绑定 tab ── */}
      {tab === 'bindings' && (
        <div>
          <div className="flex justify-end mb-4">
            <button onClick={() => setShowBindForm(!showBindForm)}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
              + 新建绑定
            </button>
          </div>

          {showBindForm && (
            <form onSubmit={handleCreateBinding} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6 space-y-4">
              <h3 className="font-semibold text-gray-900">新建网站绑定</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>网站 *</label>
                  <select required className={inputCls} value={bindForm.website_id}
                    onChange={e => setBindForm({ ...bindForm, website_id: e.target.value })}>
                    <option value="">选择网站...</option>
                    {websites?.map((w: any) => <option key={w.id} value={w.id}>{w.domain}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelCls}>MCC 账号 *</label>
                  <select required className={inputCls} value={bindForm.manager_account_id}
                    onChange={e => setBindForm({ ...bindForm, manager_account_id: e.target.value })}>
                    <option value="">选择 MCC...</option>
                    {managers?.map((m: any) => <option key={m.id} value={m.id}>{m.manager_name || m.login_customer_id}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelCls}>广告客户账号 *</label>
                  <select required className={inputCls} value={bindForm.ads_account_id}
                    onChange={e => {
                      const acct = adsAccounts?.find((a: any) => a.id === e.target.value)
                      setBindForm({ ...bindForm, ads_account_id: e.target.value, customer_id: acct?.customer_id || '' })
                    }}>
                    <option value="">选择广告账号...</option>
                    {adsAccounts?.map((a: any) => <option key={a.id} value={a.id}>{a.account_name || a.customer_id}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelCls}>Customer ID（自动填入）</label>
                  <input className={inputCls} value={bindForm.customer_id} readOnly
                    placeholder="选择广告账号后自动填入" />
                </div>
                <div>
                  <label className={labelCls}>每日预算上限 $（可选）</label>
                  <input type="number" step="0.01" className={inputCls} value={bindForm.daily_budget_cap}
                    placeholder="留空则不限制"
                    onChange={e => setBindForm({ ...bindForm, daily_budget_cap: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {saving ? '保存中...' : '保存'}
                </button>
                <button type="button" onClick={() => setShowBindForm(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200">
                  取消
                </button>
              </div>
            </form>
          )}

          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">网站与广告账号绑定（{bindings?.length ?? 0}）</h3>
            </div>
            <div className="divide-y divide-gray-50">
              {!bindings && <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>}
              {bindings?.length === 0 && <p className="px-6 py-8 text-center text-gray-400 text-sm">暂无绑定，点击右上角新建</p>}
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
                        预算上限: {b.daily_budget_cap ? `$${b.daily_budget_cap}/天` : '未设置'} · 每日最多 {b.max_actions_per_day} 条操作
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {b.safety_paused && <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">🛡️ 安全暂停</span>}
                      <button onClick={() => handleSync(b.website_id)}
                        className="px-3 py-1.5 text-xs bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100">
                        同步数据
                      </button>
                      <button onClick={() => handleOptimize(b.website_id)}
                        className="px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">
                        触发优化
                      </button>
                      <button onClick={() => handleToggleAutopilot(b.id, b.ai_autopilot_enabled)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${b.ai_autopilot_enabled ? 'bg-green-500' : 'bg-gray-300'}`}>
                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${b.ai_autopilot_enabled ? 'translate-x-6' : 'translate-x-1'}`} />
                      </button>
                      <span className="text-xs text-gray-500 w-16">{b.ai_autopilot_enabled ? 'AI 托管中' : '已关闭'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── MCC tab ── */}
      {tab === 'managers' && (
        <div>
          <div className="flex justify-end mb-4">
            <button onClick={() => setShowMccForm(!showMccForm)}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
              + 添加 MCC
            </button>
          </div>
          {showMccForm && (
            <form onSubmit={handleCreateManager} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6 space-y-4">
              <h3 className="font-semibold text-gray-900">添加 MCC 经理账号</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>login_customer_id *（不带横线）</label>
                  <input required className={inputCls} placeholder="如：9999999999"
                    value={mccForm.login_customer_id}
                    onChange={e => setMccForm({ ...mccForm, login_customer_id: e.target.value.replace(/-/g, '') })} />
                </div>
                <div>
                  <label className={labelCls}>账号名称</label>
                  <input className={inputCls} placeholder="如：GLS 代理商 MCC"
                    value={mccForm.manager_name}
                    onChange={e => setMccForm({ ...mccForm, manager_name: e.target.value })} />
                </div>
                <div>
                  <label className={labelCls}>授权邮箱</label>
                  <input type="email" className={inputCls} placeholder="kingman.chang@gmail.com"
                    value={mccForm.oauth_user_email}
                    onChange={e => setMccForm({ ...mccForm, oauth_user_email: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {saving ? '保存中...' : '保存'}
                </button>
                <button type="button" onClick={() => setShowMccForm(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg">取消</button>
              </div>
            </form>
          )}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">MCC 经理账号（{managers?.length ?? 0}）</h3>
            </div>
            <div className="divide-y divide-gray-50">
              {managers?.length === 0 && <p className="px-6 py-8 text-center text-gray-400 text-sm">暂无 MCC 账号，点击右上角添加</p>}
              {managers?.map((m: any) => (
                <div key={m.id} className="px-6 py-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{m.manager_name ?? '未命名'}</p>
                    <p className="text-sm text-gray-500 mt-0.5">login_customer_id: <span className="font-mono">{m.login_customer_id}</span></p>
                    {m.oauth_user_email && <p className="text-xs text-gray-400 mt-0.5">{m.oauth_user_email}</p>}
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${m.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {m.status === 'active' ? '已授权' : m.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── 广告账号 tab ── */}
      {tab === 'ads' && (
        <div>
          <div className="flex justify-end mb-4">
            <button onClick={() => setShowAdsForm(!showAdsForm)}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
              + 添加广告账号
            </button>
          </div>
          {showAdsForm && (
            <form onSubmit={handleCreateAdsAccount} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6 space-y-4">
              <h3 className="font-semibold text-gray-900">添加广告客户账号</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>所属 MCC *</label>
                  <select required className={inputCls} value={adsForm.manager_account_id}
                    onChange={e => setAdsForm({ ...adsForm, manager_account_id: e.target.value })}>
                    <option value="">选择 MCC...</option>
                    {managers?.map((m: any) => <option key={m.id} value={m.id}>{m.manager_name || m.login_customer_id}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelCls}>Customer ID *（不带横线）</label>
                  <input required className={inputCls} placeholder="如：5676857258"
                    value={adsForm.customer_id}
                    onChange={e => setAdsForm({ ...adsForm, customer_id: e.target.value.replace(/-/g, '') })} />
                </div>
                <div>
                  <label className={labelCls}>账号名称</label>
                  <input className={inputCls} placeholder="如：GLS-深圳汇纵-robotlyne"
                    value={adsForm.account_name}
                    onChange={e => setAdsForm({ ...adsForm, account_name: e.target.value })} />
                </div>
                <div>
                  <label className={labelCls}>货币</label>
                  <input className={inputCls} value={adsForm.currency_code}
                    onChange={e => setAdsForm({ ...adsForm, currency_code: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {saving ? '保存中...' : '保存'}
                </button>
                <button type="button" onClick={() => setShowAdsForm(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg">取消</button>
              </div>
            </form>
          )}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">广告客户账号（{adsAccounts?.length ?? 0}）</h3>
            </div>
            <div className="divide-y divide-gray-50">
              {adsAccounts?.length === 0 && <p className="px-6 py-8 text-center text-gray-400 text-sm">暂无广告账号，点击右上角添加</p>}
              {adsAccounts?.map((a: any) => (
                <div key={a.id} className="px-6 py-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{a.account_name ?? '未命名'}</p>
                    <p className="text-sm text-gray-500 mt-0.5">
                      customer_id: <span className="font-mono">{a.customer_id}</span>
                      {a.currency_code && ` · ${a.currency_code}`}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${a.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {a.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
