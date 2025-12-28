'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: string;
  status?: 'normal' | 'warning' | 'critical';
  color?: 'blue' | 'amber' | 'green' | 'red';
}

export const StatCard = ({
  title,
  value,
  icon,
  trend,
  status = 'normal',
  color = 'blue',
}: StatCardProps) => {
  const iconColorClasses = {
    blue: 'bg-blue-500/10 text-blue-600',
    amber: 'bg-amber-500/10 text-amber-600',
    green: 'bg-green-500/10 text-green-600',
    red: 'bg-red-500/10 text-red-600',
  };

  const statusClasses = {
    normal: '',
    warning: 'ring-2 ring-amber-400/50',
    critical: 'ring-2 ring-red-500/50 shadow-red-500/20 shadow-lg',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card className={cn(
        'transition-all duration-200 hover:shadow-md',
        statusClasses[status],
        status === 'critical' && 'animate-pulse'
      )}>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{title}</p>
              <p className="text-2xl font-semibold tracking-tight">{value}</p>
              {trend && (
                <p className="text-sm text-green-600 font-medium">{trend}</p>
              )}
            </div>
            <div className={cn('p-2.5 rounded-lg', iconColorClasses[color])}>
              {icon}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
