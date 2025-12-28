'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, X, Check, CheckCheck, AlertTriangle, Lightbulb,
  Train, Car, Users, Clock, MessageCircle, Send,
  Volume2, VolumeX, ChevronDown
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Alert, Recommendation } from '@/types';

interface StaffNotification {
  id: string;
  type: 'alert' | 'recommendation' | 'update' | 'transport';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  action?: string;
  timestamp: Date;
  read: boolean;
  acknowledged: boolean;
  source?: string;
}

interface StaffNotificationsProps {
  alerts: Alert[];
  recommendations: Recommendation[];
  isOpen: boolean;
  onClose: () => void;
  onAcknowledge?: (id: string) => void;
}

export const StaffNotifications = ({
  alerts,
  recommendations,
  isOpen,
  onClose,
  onAcknowledge
}: StaffNotificationsProps) => {
  const [notifications, setNotifications] = useState<StaffNotification[]>([]);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread' | 'critical'>('all');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Convert alerts and recommendations to notifications
  useEffect(() => {
    const newNotifications: StaffNotification[] = [];

    // Add alerts
    alerts.forEach(alert => {
      newNotifications.push({
        id: alert.alert_id,
        type: 'alert',
        priority: alert.level === 'emergency' ? 'critical' :
                  alert.level === 'critical' ? 'critical' :
                  alert.level === 'warning' ? 'high' : 'medium',
        title: alert.title,
        message: alert.message,
        action: alert.suggested_actions[0],
        timestamp: new Date(alert.timestamp),
        read: false,
        acknowledged: false,
        source: alert.zone_id || alert.gate_id
      });
    });

    // Add recommendations
    recommendations.forEach(rec => {
      newNotifications.push({
        id: rec.recommendation_id,
        type: 'recommendation',
        priority: rec.confidence > 0.9 ? 'high' : 'medium',
        title: rec.title,
        message: rec.description,
        action: rec.impact,
        timestamp: new Date(rec.timestamp),
        read: false,
        acknowledged: false
      });
    });

    // Sort by timestamp, newest first
    newNotifications.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    setNotifications(prev => {
      // Merge with existing, preserving read/acknowledged status
      const existingIds = new Set(prev.map(n => n.id));
      const merged = [...prev];

      newNotifications.forEach(newNotif => {
        if (!existingIds.has(newNotif.id)) {
          merged.unshift(newNotif);
          // Play sound for new critical notifications
          if (soundEnabled && newNotif.priority === 'critical') {
            playNotificationSound();
          }
        }
      });

      return merged.slice(0, 50); // Keep last 50 notifications
    });
  }, [alerts, recommendations, soundEnabled]);

  // Auto-scroll to latest
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [notifications]);

  const playNotificationSound = () => {
    try {
      const audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch {
      // Audio not supported
    }
  };

  const handleAcknowledge = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, acknowledged: true, read: true } : n)
    );
    onAcknowledge?.(id);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const getIcon = (notification: StaffNotification) => {
    switch (notification.type) {
      case 'alert':
        return <AlertTriangle className="w-5 h-5" />;
      case 'recommendation':
        return <Lightbulb className="w-5 h-5" />;
      case 'transport':
        return <Train className="w-5 h-5" />;
      default:
        return <MessageCircle className="w-5 h-5" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-500 text-white';
      case 'high':
        return 'bg-orange-500 text-white';
      case 'medium':
        return 'bg-blue-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'unread') return !n.read;
    if (filter === 'critical') return n.priority === 'critical';
    return true;
  });

  const unreadCount = notifications.filter(n => !n.read).length;
  const criticalCount = notifications.filter(n => n.priority === 'critical' && !n.acknowledged).length;

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);

    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins} min ago`;
    if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 300 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 300 }}
      className="fixed right-0 top-0 h-full w-full max-w-md bg-background border-l shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b bg-muted/30">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            <h2 className="font-semibold text-lg">Staff Notifications</h2>
            {unreadCount > 0 && (
              <Badge variant="destructive">{unreadCount}</Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSoundEnabled(!soundEnabled)}
            >
              {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </Button>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2">
          {(['all', 'unread', 'critical'] as const).map(f => (
            <Button
              key={f}
              variant={filter === f ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(f)}
              className="text-xs"
            >
              {f === 'all' && 'All'}
              {f === 'unread' && `Unread (${unreadCount})`}
              {f === 'critical' && (
                <>
                  Critical
                  {criticalCount > 0 && (
                    <span className="ml-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  )}
                </>
              )}
            </Button>
          ))}
        </div>
      </div>

      {/* Notifications List - WhatsApp Style */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[url('/chat-bg.png')] bg-repeat">
        <AnimatePresence>
          {filteredNotifications.length === 0 ? (
            <div className="text-center text-muted-foreground py-12">
              <Bell className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No notifications</p>
            </div>
          ) : (
            filteredNotifications.map((notification, index) => (
              <motion.div
                key={notification.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -100 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => markAsRead(notification.id)}
                className={cn(
                  'rounded-lg p-3 shadow-sm max-w-[85%] cursor-pointer transition-all',
                  notification.priority === 'critical' && !notification.acknowledged
                    ? 'bg-red-50 border-2 border-red-300 animate-pulse ml-auto'
                    : notification.type === 'recommendation'
                    ? 'bg-blue-50 border border-blue-200 ml-auto'
                    : 'bg-white border ml-auto',
                  notification.read && 'opacity-75'
                )}
              >
                {/* Message Header */}
                <div className="flex items-start gap-2 mb-2">
                  <div className={cn(
                    'p-1.5 rounded-full',
                    getPriorityColor(notification.priority)
                  )}>
                    {getIcon(notification)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-sm truncate">
                        {notification.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {formatTime(notification.timestamp)}
                      </span>
                    </div>
                    {notification.source && (
                      <span className="text-[10px] text-muted-foreground">
                        {notification.source}
                      </span>
                    )}
                  </div>
                </div>

                {/* Message Body */}
                <p className="text-sm text-muted-foreground mb-2">
                  {notification.message}
                </p>

                {/* Action */}
                {notification.action && (
                  <div className="bg-primary/5 rounded p-2 mb-2">
                    <p className="text-xs font-medium text-primary">
                      Recommended: {notification.action}
                    </p>
                  </div>
                )}

                {/* Footer with actions */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    {notification.acknowledged ? (
                      <>
                        <CheckCheck className="w-3 h-3 text-blue-500" />
                        <span>Acknowledged</span>
                      </>
                    ) : notification.read ? (
                      <>
                        <CheckCheck className="w-3 h-3" />
                        <span>Read</span>
                      </>
                    ) : (
                      <>
                        <Check className="w-3 h-3" />
                        <span>Delivered</span>
                      </>
                    )}
                  </div>

                  {!notification.acknowledged && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-6 text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAcknowledge(notification.id);
                      }}
                    >
                      Acknowledge
                    </Button>
                  )}
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions Footer */}
      <div className="p-4 border-t bg-muted/30">
        <div className="grid grid-cols-3 gap-2">
          <Button variant="outline" size="sm" className="text-xs">
            <Users className="w-3 h-3 mr-1" />
            Dispatch
          </Button>
          <Button variant="outline" size="sm" className="text-xs">
            <Clock className="w-3 h-3 mr-1" />
            Delay Event
          </Button>
          <Button variant="destructive" size="sm" className="text-xs">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Emergency
          </Button>
        </div>
      </div>
    </motion.div>
  );
};

// Floating notification button
export const NotificationButton = ({
  unreadCount,
  criticalCount,
  onClick
}: {
  unreadCount: number;
  criticalCount: number;
  onClick: () => void;
}) => {
  return (
    <Button
      variant="outline"
      size="icon"
      onClick={onClick}
      className={cn(
        'relative',
        criticalCount > 0 && 'animate-pulse border-red-500'
      )}
    >
      <Bell className="w-5 h-5" />
      {unreadCount > 0 && (
        <span className={cn(
          'absolute -top-1 -right-1 w-5 h-5 rounded-full text-[10px] flex items-center justify-center text-white',
          criticalCount > 0 ? 'bg-red-500' : 'bg-primary'
        )}>
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </Button>
  );
};
