'use client'
import useSWR from 'swr'
import { api } from '@/lib/api'

const SEVERITY_COLOR: Record<string, string> = {
  low: 'bg-blue-100 text-blue-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-red-100 text-red-700',
}

export default function SafetyPage() {
  const { data: bindings } = useSWR('bindings', api.listBindings)
  const pausedSites = bindings?.filter((b: any) => b.safety_paused) ?? []

  return (
    <div className="p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">异常中心</h2>
        <p className="text-sm text-gray-500 mt-1">查看安全事件、风控拦截和自动暂停状态</p>
      </div>

      {pausedSites.length > 0 && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-5">
          <h3 className="font-semibold text-red-800 mb-3">⚠️ 以下网站已被安全暂停</h3>
          <div className="space-y-2">
            {pausedSites.map((b: any) => (
              <div key={b.id} className="flex items-center justify-between bg-white rounded-lg px-4 py-3">
                <div>
                  <p className="font-medium text-gray-900">{b.websites?.domain ?? b.website_id}</p>
                  <p className="text-sm text-gray-500">customer_id: {b.customer_id}</p>
                </div>
                <span className="text-xs text-red-600 font-medium">已暂停</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-red-600 mt-3">
            如需恢复，请在后端数据库将对应绑定的 safety_paused 设为 false，确认问题已解决后再开启。
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">当前托管网站</p>
          <p className="text-2xl font-bold text-green-600 mt-1">
            {bindings?.filter((b: any) => b.ai_autopilot_enabled && !b.safety_paused).length ?? '-'}
          </p>
          <p className="text-xs text-gray-400 mt-1">正常运行</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">安全暂停</p>
          <p className="text-2xl font-bold text-red-600 mt-1">{pausedSites.length}</p>
          <p className="text-xs text-gray-400 mt-1">需要人工检查</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">当前模式</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">验证模式</p>
          <p className="text-xs text-gray-400 mt-1">validate_only = true</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-6 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">风控规则说明</h3>
        </div>
        <div className="px-6 py-4 space-y-3">
          {[
            ['API 连续失败 3 次', '自动暂停当前网站执行，写入 safety_events', 'high'],
            ['单日花费超过预算上限', '停止预算相关动作并记录', 'high'],
            ['final_url 域名不匹配', '直接拒绝，不执行该动作', 'high'],
            ['跨 customer_id 操作', '拒绝执行并标记高风险', 'high'],
            ['每日 mutate 超过上限', '停止当天所有执行', 'medium'],
            ['预算单次调整超过 15%', '拦截该动作', 'medium'],
            ['否定品牌词或核心词', '拦截该动作', 'medium'],
          ].map(([rule, action, level]) => (
            <div key={rule} className="flex items-start gap-3">
              <span className={`mt-0.5 px-2 py-0.5 text-xs rounded-full shrink-0 ${SEVERITY_COLOR[level]}`}>{level}</span>
              <div>
                <p className="text-sm font-medium text-gray-900">{rule}</p>
                <p className="text-xs text-gray-500">{action}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
