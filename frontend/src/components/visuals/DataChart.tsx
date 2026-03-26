"use client";

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
  const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
  const textColor = isDark ? '#94A3B8' : '#64748B';

  const renderTooltip = (props: any) => {
    const { active, payload, label } = props;
    if (active && payload && payload.length) {
      return (
        <div className="glass p-4 rounded-2xl border-border/20 shadow-2xl backdrop-blur-2xl min-w-[160px]">
          <p className="text-[10px] font-black uppercase tracking-[2px] text-text-secondary mb-3 border-b border-border/10 pb-2">{label}</p>
          <div className="space-y-2">
            {payload.map((entry: any, i: number) => (
              <div key={i} className="flex items-center justify-between space-x-4">
                <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span className="text-[11px] font-bold text-text-primary uppercase tracking-tight">{entry.name}</span>
                </div>
                <span className="text-[11px] font-black text-[var(--accent)] tabular-nums">{entry.value.toLocaleString()}</span>
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
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 10, fontWeight: 800 }}
            dy={10}
            textAnchor="end"
            interval={0}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 10, fontWeight: 800 }}
            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value}
          />
          <Tooltip cursor={{ fill: 'var(--accent)', opacity: 0.05 }} content={renderTooltip} />
          <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: '30px', fontSize: '9px', fontWeight: '900', textTransform: 'uppercase', letterSpacing: '2px' }} />
          {chart.series.map((s, i) => (
            <Bar 
              key={s.name} 
              dataKey={s.name} 
              fill={COLORS[i % COLORS.length]} 
              radius={[4, 4, 0, 0]} 
              barSize={Math.max(16, 80 / data.length)}
            />
          ))}
        </BarChart>
      ) : chart.type === 'pie' ? (
        <PieChart>
          <Pie
            data={data.map((d, i) => ({ name: d.name, value: d[chart.series[0].name] }))}
            cx="50%"
            cy="50%"
            innerRadius="65%"
            outerRadius="85%"
            paddingAngle={8}
            dataKey="value"
            animationBegin={0}
            animationDuration={1500}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0.1)" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip content={renderTooltip} />
          <Legend verticalAlign="bottom" align="center" iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '9px', fontWeight: '900', textTransform: 'uppercase', letterSpacing: '2px' }} />
        </PieChart>
      ) : chart.type === 'area' ? (
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            {chart.series.map((s, i) => (
              <linearGradient key={`grad-${i}`} id={`color-${i}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.4}/>
                <stop offset="95%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0}/>
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 10, fontWeight: 800 }}
            dy={10}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 10, fontWeight: 800 }}
          />
          <Tooltip content={renderTooltip} />
          <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: '30px', fontSize: '9px', fontWeight: '900', textTransform: 'uppercase', letterSpacing: '2px' }} />
          {chart.series.map((s, i) => (
            <Area 
              key={s.name} 
              type="monotone" 
              dataKey={s.name} 
              stroke={COLORS[i % COLORS.length]} 
              fillOpacity={1} 
              fill={`url(#color-${i})`} 
              strokeWidth={3}
              animationDuration={2000}
            />
          ))}
        </AreaChart>
      ) : (
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 10, fontWeight: 800 }}
            dy={10}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: textColor, fontSize: 10, fontWeight: 800 }}
          />
          <Tooltip content={renderTooltip} />
          <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: '30px', fontSize: '9px', fontWeight: '900', textTransform: 'uppercase', letterSpacing: '2px' }} />
          {chart.series.map((s, i) => (
            <Line 
              key={s.name} 
              type="monotone" 
              dataKey={s.name} 
              stroke={COLORS[i % COLORS.length]} 
              strokeWidth={4}
              dot={{ r: 4, strokeWidth: 2, fill: isDark ? '#05070A' : '#FFFFFF' }}
              activeDot={{ r: 7, strokeWidth: 0 }}
              animationDuration={2000}
            />
          ))}
        </LineChart>
      )}
    </ResponsiveContainer>
  );
};

