'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Users, MapPin, Play, ChevronRight, Shield,
  BarChart3, Bell, Zap, Building2, Radio, Calendar, Upload
} from 'lucide-react';
import Link from 'next/link';
import type { Scenario } from '@/types';
import { api } from '@/lib/api';
import { formatNumber } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function HomePage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadScenarios = async () => {
      try {
        setError(null);
        const data = await api.getScenarios();
        setScenarios(data);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to load scenarios';
        console.error('Failed to load scenarios:', errorMsg);
        setError(errorMsg);
      } finally {
        setIsLoading(false);
      }
    };

    loadScenarios();
  }, []);

  const getVenueIcon = (venueId: string) => {
    if (venueId.includes('bukit-jalil')) return '🏟️';
    if (venueId.includes('axiata')) return '🎤';
    if (venueId.includes('pavilion')) return '🏬';
    return '📍';
  };

  const getEventTypeBadge = (type: string) => {
    const variants: Record<string, "default" | "secondary" | "outline"> = {
      football: 'default',
      concert: 'secondary',
      festival: 'outline',
    };
    return variants[type] || 'default';
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Radio className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">CrowdControl</h1>
              <p className="text-xs text-muted-foreground">AI-Powered Event Management</p>
            </div>
          </div>

          <nav className="flex items-center gap-2">
            <Link href="/planner">
              <Button variant="outline" size="sm">
                <Calendar className="w-4 h-4 mr-2" />
                Pre-Event Planner
              </Button>
            </Link>
            <Link href="/data-import">
              <Button variant="outline" size="sm">
                <Upload className="w-4 h-4 mr-2" />
                Import Data
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container py-12 md:py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <Badge variant="secondary" className="mb-4">
            AI-Powered
          </Badge>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Predict. Simulate. Protect.
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            AI-powered crowd simulation and management for Malaysian events.
            Identify risks before they happen, get real-time recommendations,
            and keep your attendees safe.
          </p>
        </motion.div>

        {/* Feature Cards */}
        <div className="mx-auto mt-12 grid max-w-5xl gap-6 md:grid-cols-3">
          {[
            {
              icon: Shield,
              title: 'Risk Detection',
              desc: 'Identify bottlenecks and overcrowding before they become dangerous',
              color: 'text-green-600'
            },
            {
              icon: BarChart3,
              title: 'Real-time Analytics',
              desc: 'Live density heatmaps and crowd flow visualization',
              color: 'text-blue-600'
            },
            {
              icon: Bell,
              title: 'Smart Alerts',
              desc: 'AI-powered recommendations for gate and crowd management',
              color: 'text-amber-600'
            },
          ].map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 + 0.2 }}
            >
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader>
                  <feature.icon className={`h-10 w-10 ${feature.color}`} />
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{feature.desc}</CardDescription>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Scenarios Section */}
      <section className="border-t bg-muted/50 py-12">
        <div className="container">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold tracking-tight">Demo Scenarios</h2>
            <p className="text-muted-foreground">
              Select a scenario to run the crowd simulation
            </p>
          </div>

          {isLoading ? (
            <div className="grid gap-6 md:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-8 w-8 rounded bg-muted" />
                    <div className="mt-4 h-5 w-3/4 rounded bg-muted" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-4 w-full rounded bg-muted" />
                    <div className="mt-2 h-4 w-2/3 rounded bg-muted" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : error ? (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="p-6 text-center">
                <p className="text-red-600 font-medium">Failed to load scenarios</p>
                <p className="text-sm text-red-500 mt-1">{error}</p>
                <p className="text-sm text-muted-foreground mt-4">
                  Make sure the backend is running on <code className="bg-muted px-1 rounded">http://localhost:8000</code>
                </p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </Button>
              </CardContent>
            </Card>
          ) : scenarios.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center text-muted-foreground">
                No scenarios found. Check the backend connection.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6 md:grid-cols-3">
              {scenarios.map((scenario, i) => (
                <motion.div
                  key={scenario.scenario_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Link href={`/dashboard/${scenario.scenario_id}`}>
                    <Card className="group h-full cursor-pointer transition-all hover:border-primary hover:shadow-lg">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <span className="text-4xl">{getVenueIcon(scenario.venue_id)}</span>
                          <Badge variant={getEventTypeBadge(scenario.event_type)}>
                            {scenario.event_type}
                          </Badge>
                        </div>
                        <CardTitle className="mt-4 group-hover:text-primary transition-colors">
                          {scenario.name}
                        </CardTitle>
                        <CardDescription className="line-clamp-2">
                          {scenario.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Users className="h-4 w-4" />
                            <span>{formatNumber(scenario.expected_attendance)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Building2 className="h-4 w-4" />
                            <span className="truncate">{scenario.venue_id}</span>
                          </div>
                        </div>

                        <div className="mt-4 flex items-center gap-2">
                          <Button
                            variant="default"
                            size="sm"
                            className="w-full group-hover:bg-primary"
                          >
                            <Play className="mr-2 h-4 w-4" />
                            Run Simulation
                            <ChevronRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Capabilities Section */}
      <section className="container py-12">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-8 text-center text-2xl font-semibold">System Capabilities</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              { title: 'Scalable Simulation', desc: 'From 1,000 to 100,000+ attendees' },
              { title: 'Malaysian Venues', desc: 'Bukit Jalil, Axiata Arena, Pavilion KL' },
              { title: 'No Hardware Required', desc: 'Uses existing ticketing & schedule data' },
              { title: 'Emergency Mode', desc: 'Evacuation simulation with exit routing' },
              { title: 'Real-time Alerts', desc: 'Instant notifications for event staff' },
              { title: 'AI Recommendations', desc: 'Smart suggestions for crowd management' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg border p-4">
                <Zap className="h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">{item.title}</p>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container text-center text-sm text-muted-foreground">
          <p>AI-Powered Crowd Control System for Malaysian Events</p>
          <p className="mt-1">Built with Next.js, FastAPI, and shadcn/ui</p>
        </div>
      </footer>
    </div>
  );
}
