'use client';

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface AttendanceChartProps {
  currentMinute: number;
  totalInside: number;
  totalQueuing: number;
  capacity: number;
  isEmergencyMode?: boolean;
}

// Store history for chart
const historyData: { minute: number; inside: number; queuing: number }[] = [];

export const AttendanceChart = ({
  currentMinute,
  totalInside,
  totalQueuing,
  capacity,
  isEmergencyMode = false,
}: AttendanceChartProps) => {
  // Update history
  useMemo(() => {
    const lastEntry = historyData[historyData.length - 1];
    if (!lastEntry || Math.floor(currentMinute) > Math.floor(lastEntry.minute)) {
      historyData.push({
        minute: Math.floor(currentMinute),
        inside: totalInside,
        queuing: totalQueuing,
      });
      // Keep only last 60 data points
      if (historyData.length > 60) {
        historyData.shift();
      }
    }
  }, [currentMinute, totalInside, totalQueuing]);

  const chartData = historyData.length > 0 ? historyData : [
    { minute: 0, inside: 0, queuing: 0 },
  ];

  const formatMinute = (minute: number) => {
    const hours = Math.floor(minute / 60);
    const mins = minute % 60;
    return `${hours}:${mins.toString().padStart(2, '0')}`;
  };

  return (
    <Card className={isEmergencyMode ? 'ring-2 ring-red-500' : ''}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Attendance Over Time</CardTitle>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-muted-foreground">Inside</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <span className="text-muted-foreground">Queuing</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-red-500 border-dashed" style={{ borderTop: '2px dashed' }} />
              <span className="text-muted-foreground">Capacity</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="insideGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="queuingGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>

            <XAxis
              dataKey="minute"
              tickFormatter={formatMinute}
              tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
              axisLine={{ stroke: 'hsl(var(--border))' }}
              tickLine={false}
            />

            <YAxis
              tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                fontSize: '12px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: number, name: string) => [
                value.toLocaleString(),
                name === 'inside' ? 'Inside Venue' : 'In Queue',
              ]}
              labelFormatter={(label) => `Time: ${formatMinute(label)}`}
            />

            {/* Capacity reference line */}
            {capacity > 0 && (
              <ReferenceLine
                y={capacity}
                stroke="#ef4444"
                strokeDasharray="5 5"
                label={{ value: 'Capacity', position: 'right', fontSize: 10, fill: '#ef4444' }}
              />
            )}

            <Area
              type="monotone"
              dataKey="queuing"
              stroke="#f59e0b"
              fill="url(#queuingGradient)"
              strokeWidth={2}
            />

            <Area
              type="monotone"
              dataKey="inside"
              stroke="hsl(var(--primary))"
              fill="url(#insideGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
