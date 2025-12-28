'use client';

import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import type { Venue, ZoneState, GateState } from '@/types';
import { getRiskColor, getRiskBgColor, formatNumber, cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface VenueMapProps {
  venue: Venue;
  zoneStates: Record<string, ZoneState>;
  gateStates: Record<string, GateState>;
  isEmergencyMode?: boolean;
  onZoneClick?: (zoneId: string) => void;
  selectedZone?: string | null;
}

export const VenueMap = ({
  venue,
  zoneStates,
  gateStates,
  isEmergencyMode = false,
  onZoneClick,
  selectedZone
}: VenueMapProps) => {
  const [hoveredZone, setHoveredZone] = useState<string | null>(null);

  // Generate zone positions based on venue type
  const zonePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number; width: number; height: number }> = {};

    if (venue.venue_type === 'stadium') {
      // Stadium layout - oval with stands
      venue.zones.forEach((zone) => {
        if (zone.zone_id.includes('north')) {
          positions[zone.zone_id] = { x: 150, y: 20, width: 200, height: 60 };
        } else if (zone.zone_id.includes('south')) {
          positions[zone.zone_id] = { x: 150, y: 320, width: 200, height: 60 };
        } else if (zone.zone_id.includes('east')) {
          positions[zone.zone_id] = { x: 370, y: 120, width: 60, height: 160 };
        } else if (zone.zone_id.includes('west')) {
          positions[zone.zone_id] = { x: 70, y: 120, width: 60, height: 160 };
        } else if (zone.zone_id.includes('vip')) {
          positions[zone.zone_id] = { x: 200, y: 80, width: 100, height: 40 };
        } else if (zone.zone_id.includes('parking')) {
          positions[zone.zone_id] = { x: 20, y: 350, width: 80, height: 40 };
        } else if (zone.zone_id.includes('lrt')) {
          positions[zone.zone_id] = { x: 400, y: 350, width: 80, height: 40 };
        }
      });
    } else if (venue.venue_type === 'arena') {
      // Arena layout - rectangular
      positions['standing-a'] = { x: 180, y: 150, width: 140, height: 80 };
      positions['standing-b'] = { x: 180, y: 240, width: 140, height: 60 };
      positions['seated-lower'] = { x: 60, y: 120, width: 100, height: 180 };
      positions['seated-upper'] = { x: 340, y: 120, width: 100, height: 180 };
      positions['vip-section'] = { x: 200, y: 60, width: 100, height: 40 };
      positions['main-concourse'] = { x: 150, y: 320, width: 200, height: 50 };
      positions['merch-area'] = { x: 60, y: 320, width: 70, height: 50 };
      positions['food-court'] = { x: 370, y: 320, width: 70, height: 50 };
    } else {
      // Convention/Festival layout - multi-level
      positions['centre-court'] = { x: 150, y: 150, width: 200, height: 100 };
      positions['level-1'] = { x: 100, y: 270, width: 300, height: 50 };
      positions['level-2'] = { x: 100, y: 330, width: 300, height: 40 };
      positions['level-3'] = { x: 100, y: 380, width: 300, height: 40 };
      positions['food-republic'] = { x: 50, y: 150, width: 80, height: 80 };
      positions['outdoor-plaza'] = { x: 370, y: 150, width: 80, height: 80 };
    }

    return positions;
  }, [venue]);

  const hoveredState = hoveredZone ? zoneStates[hoveredZone] : null;
  const hoveredZoneData = hoveredZone ? venue.zones.find(z => z.zone_id === hoveredZone) : null;

  return (
    <Card className={cn(
      'transition-all duration-300',
      isEmergencyMode && 'ring-2 ring-red-500'
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            Venue Map
            {isEmergencyMode && (
              <Badge variant="emergency" className="ml-2">
                EMERGENCY
              </Badge>
            )}
          </CardTitle>
          {hoveredZoneData && (
            <div className="text-sm text-muted-foreground">
              <span className="font-medium">{hoveredZoneData.name}</span>
              <span className="mx-2">•</span>
              <span>{formatNumber(hoveredState?.current_occupancy || 0)} / {formatNumber(hoveredZoneData.capacity)}</span>
              <span className="mx-2">•</span>
              <span>{(hoveredState?.density || 0).toFixed(1)}/m²</span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="relative">
          <svg viewBox="0 0 500 420" className="w-full h-[380px]">
            {/* Background */}
            <rect x="0" y="0" width="500" height="420" fill="hsl(var(--muted))" rx="8" />

            {/* Grid pattern for professional look */}
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="hsl(var(--border))" strokeWidth="0.5" opacity="0.5" />
              </pattern>
            </defs>
            <rect x="0" y="0" width="500" height="420" fill="url(#grid)" />

            {/* Venue outline */}
            {venue.venue_type === 'stadium' && (
              <ellipse
                cx="250"
                cy="200"
                rx="180"
                ry="150"
                fill="none"
                stroke="hsl(var(--border))"
                strokeWidth="2"
              />
            )}

            {/* Zones */}
            {venue.zones.map((zone) => {
              const pos = zonePositions[zone.zone_id];
              if (!pos) return null;

              const state = zoneStates[zone.zone_id];
              const riskLevel = state?.risk_level || 'safe';
              const density = state?.density || 0;
              const occupancy = state?.current_occupancy || 0;
              const isHovered = hoveredZone === zone.zone_id;
              const isSelected = selectedZone === zone.zone_id;

              return (
                <motion.g
                  key={zone.zone_id}
                  onMouseEnter={() => setHoveredZone(zone.zone_id)}
                  onMouseLeave={() => setHoveredZone(null)}
                  onClick={() => onZoneClick?.(zone.zone_id)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Zone rectangle */}
                  <motion.rect
                    x={pos.x}
                    y={pos.y}
                    width={pos.width}
                    height={pos.height}
                    rx="6"
                    fill={getRiskBgColor(riskLevel)}
                    stroke={isSelected ? 'hsl(var(--primary))' : getRiskColor(riskLevel)}
                    strokeWidth={isSelected ? 3 : 2}
                    initial={{ opacity: 0 }}
                    animate={{
                      opacity: 1,
                      scale: isHovered ? 1.02 : 1,
                    }}
                    className={cn(
                      riskLevel === 'critical' && 'animate-pulse',
                      isEmergencyMode && 'animate-pulse'
                    )}
                  />

                  {/* Zone label */}
                  <text
                    x={pos.x + pos.width / 2}
                    y={pos.y + pos.height / 2 - 8}
                    textAnchor="middle"
                    className="text-xs font-medium"
                    fill="hsl(var(--foreground))"
                  >
                    {zone.name.length > 15 ? zone.name.substring(0, 15) + '...' : zone.name}
                  </text>

                  {/* Occupancy */}
                  <text
                    x={pos.x + pos.width / 2}
                    y={pos.y + pos.height / 2 + 8}
                    textAnchor="middle"
                    className="text-xs"
                    fill="hsl(var(--muted-foreground))"
                  >
                    {formatNumber(occupancy)} / {formatNumber(zone.capacity)}
                  </text>

                  {/* Density indicator */}
                  <text
                    x={pos.x + pos.width / 2}
                    y={pos.y + pos.height / 2 + 22}
                    textAnchor="middle"
                    className="text-[10px]"
                    fill="hsl(var(--muted-foreground))"
                  >
                    {density.toFixed(1)}/m²
                  </text>
                </motion.g>
              );
            })}

            {/* Gates */}
            {venue.gates.map((gate) => {
              const gateState = gateStates[gate.gate_id];
              const queueLength = gateState?.queue_length || 0;
              const isCongested = gateState?.is_congested || false;
              const isEmergencyExit = gate.is_emergency_exit;

              return (
                <g key={gate.gate_id}>
                  {/* Gate marker */}
                  <circle
                    cx={gate.location[0]}
                    cy={gate.location[1]}
                    r="14"
                    fill={isEmergencyMode && isEmergencyExit ? '#22c55e' : isCongested ? '#fef3c7' : '#dbeafe'}
                    stroke={isEmergencyMode && isEmergencyExit ? '#15803d' : isCongested ? '#f59e0b' : '#3b82f6'}
                    strokeWidth="2"
                    className={cn(
                      isEmergencyMode && isEmergencyExit && 'animate-pulse'
                    )}
                  />

                  {/* Gate icon */}
                  <text
                    x={gate.location[0]}
                    y={gate.location[1] + 4}
                    textAnchor="middle"
                    className="text-sm"
                  >
                    {isEmergencyExit ? (isEmergencyMode ? '🚨' : '🚪') : '🚪'}
                  </text>

                  {/* Queue indicator */}
                  {queueLength > 0 && !isEmergencyMode && (
                    <g>
                      <rect
                        x={gate.location[0] + 15}
                        y={gate.location[1] - 10}
                        width="45"
                        height="20"
                        rx="4"
                        fill={isCongested ? '#fef3c7' : 'hsl(var(--background))'}
                        stroke={isCongested ? '#f59e0b' : 'hsl(var(--border))'}
                      />
                      <text
                        x={gate.location[0] + 37}
                        y={gate.location[1] + 4}
                        textAnchor="middle"
                        className="text-[10px] font-medium"
                        fill="hsl(var(--foreground))"
                      >
                        {formatNumber(queueLength)}
                      </text>
                    </g>
                  )}

                  {/* Emergency exit label */}
                  {isEmergencyMode && isEmergencyExit && (
                    <text
                      x={gate.location[0]}
                      y={gate.location[1] + 28}
                      textAnchor="middle"
                      className="text-[10px] font-bold"
                      fill="#15803d"
                    >
                      EXIT
                    </text>
                  )}
                </g>
              );
            })}

            {/* Legend */}
            <g transform="translate(10, 10)">
              <rect x="0" y="0" width="240" height="30" rx="4" fill="hsl(var(--background))" fillOpacity="0.9" />
              <text x="8" y="18" className="text-[10px] font-medium" fill="hsl(var(--foreground))">Density:</text>
              {['safe', 'moderate', 'high', 'critical'].map((level, i) => (
                <g key={level} transform={`translate(${55 + i * 48}, 8)`}>
                  <rect width="14" height="14" rx="3" fill={getRiskBgColor(level)} stroke={getRiskColor(level)} strokeWidth="1.5" />
                  <text x="18" y="11" className="text-[9px] capitalize" fill="hsl(var(--muted-foreground))">{level}</text>
                </g>
              ))}
            </g>
          </svg>
        </div>
      </CardContent>
    </Card>
  );
};
