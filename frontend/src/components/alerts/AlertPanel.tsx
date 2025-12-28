'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Lightbulb, Siren, Info } from 'lucide-react';
import type { Alert, Recommendation } from '@/types';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface AlertPanelProps {
  alerts: Alert[];
  recommendations: Recommendation[];
  isEmergencyMode?: boolean;
}

export const AlertPanel = ({ alerts, recommendations, isEmergencyMode = false }: AlertPanelProps) => {
  const getLevelIcon = (level: string) => {
    if (level === 'emergency') {
      return <Siren className="w-4 h-4" />;
    }
    if (level === 'critical') {
      return <AlertTriangle className="w-4 h-4" />;
    }
    if (level === 'warning') {
      return <AlertTriangle className="w-4 h-4" />;
    }
    return <Info className="w-4 h-4" />;
  };

  const getLevelBadgeVariant = (level: string): "safe" | "moderate" | "high" | "critical" | "emergency" => {
    const variants: Record<string, "safe" | "moderate" | "high" | "critical" | "emergency"> = {
      info: 'safe',
      warning: 'moderate',
      high: 'high',
      critical: 'critical',
      emergency: 'emergency',
    };
    return variants[level] || 'safe';
  };

  const criticalAlerts = alerts.filter(a => a.level === 'critical' || a.level === 'emergency');
  const otherAlerts = alerts.filter(a => a.level !== 'critical' && a.level !== 'emergency');

  return (
    <Card className={cn(
      'transition-all duration-300',
      isEmergencyMode && 'ring-2 ring-red-500 shadow-lg shadow-red-500/20'
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Alerts & AI Insights</CardTitle>
          {alerts.length > 0 && (
            <Badge variant={criticalAlerts.length > 0 ? 'critical' : 'moderate'}>
              {alerts.length} active
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <Tabs defaultValue="alerts" className="w-full">
          <TabsList className="w-full rounded-none border-b bg-transparent px-4">
            <TabsTrigger value="alerts" className="flex-1">
              Alerts
              {criticalAlerts.length > 0 && (
                <span className="ml-2 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              )}
            </TabsTrigger>
            <TabsTrigger value="recommendations" className="flex-1">
              AI Insights
            </TabsTrigger>
          </TabsList>

          <TabsContent value="alerts" className="mt-0">
            <div className="max-h-[350px] overflow-y-auto p-4 space-y-3">
              <AnimatePresence mode="popLayout">
                {alerts.length === 0 ? (
                  <div className="text-sm text-muted-foreground text-center py-8">
                    No active alerts
                  </div>
                ) : (
                  <>
                    {/* Critical alerts first */}
                    {criticalAlerts.map((alert) => (
                      <motion.div
                        key={alert.alert_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className={cn(
                          'p-3 rounded-lg border',
                          alert.level === 'emergency' && 'bg-red-50 border-red-300 animate-pulse',
                          alert.level === 'critical' && 'bg-red-50 border-red-200'
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <div className={cn(
                            'p-1.5 rounded-full',
                            alert.level === 'emergency' ? 'bg-red-500 text-white' : 'bg-red-100 text-red-600'
                          )}>
                            {getLevelIcon(alert.level)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-sm">{alert.title}</span>
                              <Badge variant={getLevelBadgeVariant(alert.level)} className="text-[10px] px-1.5 py-0">
                                {alert.level}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">{alert.message}</p>
                            {alert.suggested_actions.length > 0 && (
                              <div className="mt-2 space-y-1">
                                {alert.suggested_actions.slice(0, 2).map((action, i) => (
                                  <div key={i} className="flex items-start gap-1.5 text-xs text-blue-700">
                                    <span className="text-blue-500 mt-0.5">→</span>
                                    {action}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}

                    {/* Other alerts */}
                    {otherAlerts.map((alert) => (
                      <motion.div
                        key={alert.alert_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className={cn(
                          'p-3 rounded-lg border',
                          alert.level === 'warning' && 'bg-amber-50 border-amber-200',
                          alert.level === 'info' && 'bg-blue-50 border-blue-200'
                        )}
                      >
                        <div className="flex items-start gap-3">
                          <div className={cn(
                            'p-1.5 rounded-full',
                            alert.level === 'warning' ? 'bg-amber-100 text-amber-600' : 'bg-blue-100 text-blue-600'
                          )}>
                            {getLevelIcon(alert.level)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-sm">{alert.title}</span>
                            </div>
                            <p className="text-xs text-muted-foreground">{alert.message}</p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </>
                )}
              </AnimatePresence>
            </div>
          </TabsContent>

          <TabsContent value="recommendations" className="mt-0">
            <div className="max-h-[350px] overflow-y-auto p-4 space-y-3">
              <AnimatePresence mode="popLayout">
                {recommendations.length === 0 ? (
                  <div className="text-sm text-muted-foreground text-center py-8">
                    No recommendations yet
                  </div>
                ) : (
                  recommendations.slice(0, 5).map((rec) => (
                    <motion.div
                      key={rec.recommendation_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-3 rounded-lg bg-primary/5 border border-primary/20"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-1.5 rounded-full bg-primary/10 text-primary">
                          <Lightbulb className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="font-medium text-sm">{rec.title}</span>
                          <p className="text-xs text-muted-foreground mt-1">{rec.description}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="text-[10px]">
                              {rec.impact}
                            </Badge>
                            <span className="text-[10px] text-muted-foreground">
                              {Math.round(rec.confidence * 100)}% confidence
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
