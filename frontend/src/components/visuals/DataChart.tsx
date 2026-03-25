import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  PieChart, 
  Pie, 
  Cell,
  Legend
} from 'recharts';
import { useAppStore } from '@/store/useAppStore';

interface ChartProps {
  chart: {
    type: 'bar' | 'line' | 'pie' | 'area';
    options?: any;
    series: { name: string, data: number[] }[];
    labels: string[];
  };
}

export const DataChart = ({ chart }: ChartProps) => {
  const { theme } = useAppStore();
  const isDark = theme === 'dark';

  // Transform data for Recharts
  const data = chart.labels.map((label, index) => {
    const obj: any = { name: label };
    chart.series.forEach(serie => {
      obj[serie.name] = serie.data[index];
    });
    return obj;
  });

  const COLORS = ['#8B5CF6', '#D946EF', '#10B981', '#F59E0B', '#EF4444'];
  const gridColor = isDark ? '#374151' : '#E5E7EB';
  const textColor = isDark ? '#9CA3AF' : '#6B7280';

  const renderTooltip = (props: any) => {
    const { active, payload, label } = props;
    if (active && payload && payload.length) {
      return (
        <div className="bg-background-secondary border border-border/60 p-4 rounded-xl shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-black uppercase tracking-widest text-text-secondary mb-2">{label}</p>
          <div className="space-y-1.5">
            {payload.map((entry: any, i: number) => (
              <div key={i} className="flex items-center space-x-3">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="text-sm font-bold text-text-primary capitalize">{entry.name}:</span>
                <span className="text-sm font-black text-accent">{entry.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      {chart.type === 'bar' ? (
        <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} strokeOpacity={0.4} />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 11, fontWeight: 700 }}
            dy={10}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 11, fontWeight: 700 }}
            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value}
          />
          <Tooltip cursor={{ fill: 'var(--accent)', opacity: 0.05 }} content={renderTooltip} />
          <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px' }} />
          {chart.series.map((s, i) => (
            <Bar 
              key={s.name} 
              dataKey={s.name} 
              fill={COLORS[i % COLORS.length]} 
              radius={[6, 6, 0, 0]} 
              barSize={Math.max(20, 120 / data.length)}
            />
          ))}
        </BarChart>
      ) : chart.type === 'pie' ? (
        <PieChart>
          <Pie
            data={data.map((d, i) => ({ name: d.name, value: d[chart.series[0].name] }))}
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="80%"
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0.1)" />
            ))}
          </Pie>
          <Tooltip content={renderTooltip} />
          <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px' }} />
        </PieChart>
      ) : (
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} strokeOpacity={0.4} />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 11, fontWeight: 700 }}
            dy={10}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 11, fontWeight: 700 }}
          />
          <Tooltip content={renderTooltip} />
          <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px' }} />
          {chart.series.map((s, i) => (
            <Line 
              key={s.name} 
              type="monotone" 
              dataKey={s.name} 
              stroke={COLORS[i % COLORS.length]} 
              strokeWidth={3}
              dot={{ r: 6, strokeWidth: 2, fill: isDark ? '#1F2937' : '#F9FAFB' }}
              activeDot={{ r: 8, strokeWidth: 0 }}
            />
          ))}
        </LineChart>
      )}
    </ResponsiveContainer>
  );
};
