'use client';

import { motion } from 'framer-motion';
import type { Zone, ZoneState } from '@/types';
import { getRiskColor, formatNumber, cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface ZoneListProps {
  zones: Zone[];
  zoneStates: Record<string, ZoneState>;
  onZoneClick?: (zoneId: string) => void;
  selectedZone?: string | null;
}

export const ZoneList = ({ zones, zoneStates, onZoneClick, selectedZone }: ZoneListProps) => {
  // Sort zones by risk level (critical first)
  const sortedZones = [...zones].sort((a, b) => {
    const riskOrder = { critical: 0, high: 1, moderate: 2, safe: 3 };
    const aRisk = zoneStates[a.zone_id]?.risk_level || 'safe';
    const bRisk = zoneStates[b.zone_id]?.risk_level || 'safe';
    return riskOrder[aRisk as keyof typeof riskOrder] - riskOrder[bRisk as keyof typeof riskOrder];
  });

  const getBadgeVariant = (level: string): "safe" | "moderate" | "high" | "critical" => {
    const variants: Record<string, "safe" | "moderate" | "high" | "critical"> = {
      safe: 'safe',
      moderate: 'moderate',
      high: 'high',
      critical: 'critical',
    };
    return variants[level] || 'safe';
  };

  const getProgressColor = (level: string) => {
    const colors: Record<string, string> = {
      safe: 'bg-green-500',
      moderate: 'bg-yellow-500',
      high: 'bg-orange-500',
      critical: 'bg-red-500',
    };
    return colors[level] || 'bg-green-500';
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Zone Status</CardTitle>
      </CardHeader>

      <CardContent className="p-0">
        <div className="max-h-[300px] overflow-y-auto">
          <div className="divide-y">
            {sortedZones.map((zone) => {
              const state = zoneStates[zone.zone_id];
              const occupancy = state?.current_occupancy || 0;
              const density = state?.density || 0;
              const riskLevel = state?.risk_level || 'safe';
              const occupancyPercent = Math.min((occupancy / zone.capacity) * 100, 100);
              const isSelected = selectedZone === zone.zone_id;

              return (
                <motion.div
                  key={zone.zone_id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={() => onZoneClick?.(zone.zone_id)}
                  className={cn(
                    'px-4 py-3 transition-colors cursor-pointer',
                    'hover:bg-muted/50',
                    isSelected && 'bg-primary/5 border-l-2 border-l-primary',
                    riskLevel === 'critical' && 'bg-red-50/50'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          'w-2 h-2 rounded-full',
                          riskLevel === 'critical' && 'animate-pulse'
                        )}
                        style={{ backgroundColor: getRiskColor(riskLevel) }}
                      />
                      <span className="text-sm font-medium">
                        {zone.name}
                      </span>
                    </div>
                    <Badge variant={getBadgeVariant(riskLevel)} className="text-[10px] px-1.5">
                      {riskLevel}
                    </Badge>
                  </div>

                  {/* Progress bar */}
                  <div className="mb-2">
                    <Progress
                      value={occupancyPercent}
                      className="h-1.5"
                      indicatorClassName={getProgressColor(riskLevel)}
                    />
                  </div>

                  {/* Stats */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>
                      {formatNumber(occupancy)} / {formatNumber(zone.capacity)}
                    </span>
                    <span className="font-medium">
                      {density.toFixed(1)}/m²
                    </span>
                    <span>
                      {occupancyPercent.toFixed(0)}%
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
