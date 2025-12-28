import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export const formatNumber = (num: number): string => {
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`;
  }
  return num.toString();
};

export const formatDensity = (density: number): string => {
  return `${density.toFixed(1)}/m²`;
};

export const formatTime = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const mins = Math.floor(minutes % 60);
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
};

export const getRiskColor = (level: string): string => {
  const colors: Record<string, string> = {
    safe: '#22c55e',
    moderate: '#eab308',
    high: '#f97316',
    critical: '#ef4444',
  };
  return colors[level] || colors.safe;
};

export const getRiskBgColor = (level: string): string => {
  const colors: Record<string, string> = {
    safe: 'rgba(34, 197, 94, 0.2)',
    moderate: 'rgba(234, 179, 8, 0.3)',
    high: 'rgba(249, 115, 22, 0.4)',
    critical: 'rgba(239, 68, 68, 0.5)',
  };
  return colors[level] || colors.safe;
};

export const getAlertColor = (level: string): string => {
  const colors: Record<string, string> = {
    info: '#3b82f6',
    warning: '#f59e0b',
    critical: '#ef4444',
    emergency: '#dc2626',
  };
  return colors[level] || colors.info;
};

export const getAlertBgColor = (level: string): string => {
  const colors: Record<string, string> = {
    info: 'bg-blue-50 border-blue-200',
    warning: 'bg-amber-50 border-amber-200',
    critical: 'bg-red-50 border-red-200',
    emergency: 'bg-red-100 border-red-300',
  };
  return colors[level] || colors.info;
};
