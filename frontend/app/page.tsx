import { LowStockList } from "@/components/dashboard/LowStockList";
import { PendingOrdersTable } from "@/components/dashboard/PendingOrdersTable";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { TodaysShipments } from "@/components/dashboard/TodaysShipments";
import { api } from "@/lib/api";

export default async function DashboardPage() {
  const data = await api.dashboardToday();
  return (
    <div className="space-y-6 max-w-7xl">
      <header>
        <h1 className="text-2xl font-bold">Bugün</h1>
        <p className="text-slate-600 text-sm">Son 24 saatin operasyonel özeti.</p>
      </header>
      <SummaryCards summary={data.summary} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <PendingOrdersTable rows={data.pending_orders} title="Bekleyen Siparişler" />
          <PendingOrdersTable rows={data.recent_orders} title="Son 24 Saatte Gelen Siparişler" />
        </div>
        <div className="space-y-6">
          <LowStockList rows={data.low_stock_items} />
          <TodaysShipments rows={data.todays_shipments} />
        </div>
      </div>
    </div>
  );
}
