"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Users, Mail, MailOpen, MousePointerClick, Percent } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get("/api/dashboard/");
        setData(response.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent"></div>
      </div>
    );
  }

  if (!data) {
    return <div className="text-center text-red-500 mt-10">Failed to load dashboard data.</div>;
  }

  const statCards = [
    { title: "Total Leads", value: data.total_leads, icon: Users, color: "text-blue-500" },
    { title: "Emails Sent", value: data.total_emails_sent, icon: Mail, color: "text-accent" },
    { title: "Emails Opened", value: data.total_emails_opened, icon: MailOpen, color: "text-yellow-500" },
    { title: "Open Rate", value: `${data.open_rate}%`, icon: Percent, color: "text-orange-500" },
    { title: "Links Clicked", value: data.total_links_clicked, icon: MousePointerClick, color: "text-purple-500" },
    { title: "Click Rate", value: `${data.click_rate}%`, icon: Percent, color: "text-pink-500" },
  ];

  const funnelData = [
    { name: "Sent", count: data.total_emails_sent },
    { name: "Opened", count: data.total_emails_opened },
    { name: "Clicked", count: data.total_links_clicked },
  ];

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];
  const categoryData = Object.keys(data.category_breakdown).map((key, index) => ({
    name: key,
    value: data.category_breakdown[key],
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
        <p className="text-gray-400">Track your email campaign performance and lead metrics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat, idx) => (
          <div key={idx} className="bg-card border border-border rounded-xl p-6 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 font-medium mb-1">{stat.title}</p>
              <h3 className="text-3xl font-bold">{stat.value}</h3>
            </div>
            <div className={`p-3 rounded-lg bg-background ${stat.color}`}>
              <stat.icon className="w-6 h-6" />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-bold mb-4">Email Engagement Funnel</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                <Bar dataKey="count" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-bold mb-4">AI Categorization Breakdown</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl p-6 overflow-hidden">
        <h3 className="text-lg font-bold mb-4">Recent Leads</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-400 uppercase bg-background">
              <tr>
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Category</th>
                <th className="px-6 py-3">Priority</th>
                <th className="px-6 py-3">Sent</th>
                <th className="px-6 py-3">Opened</th>
                <th className="px-6 py-3">Clicked</th>
                <th className="px-6 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_leads.map((lead: any) => (
                <tr key={lead.id} className="border-b border-border hover:bg-background/50 transition-colors">
                  <td className="px-6 py-4 font-medium">{lead.full_name}</td>
                  <td className="px-6 py-4 text-gray-400">{lead.email}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 rounded-full bg-blue-500/10 text-blue-500 text-xs font-semibold">
                      {lead.ai_category || "Uncategorized"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${lead.ai_priority === 'High' ? 'bg-red-500/10 text-red-500' : lead.ai_priority === 'Medium' ? 'bg-yellow-500/10 text-yellow-500' : 'bg-gray-500/10 text-gray-400'}`}>
                      {lead.ai_priority || "Low"}
                    </span>
                  </td>
                  <td className="px-6 py-4">{lead.email_sent ? "Yes" : "No"}</td>
                  <td className="px-6 py-4">{lead.email_opened ? `Yes (${lead.open_count})` : "No"}</td>
                  <td className="px-6 py-4">{lead.link_clicked ? `Yes (${lead.click_count})` : "No"}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-400">
                    {new Date(lead.submission_time).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {data.recent_leads.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                    No leads found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
