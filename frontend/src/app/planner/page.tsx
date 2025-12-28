'use client';

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Play, Plus, Trash2, Download, Upload,
  Clock, Users, Car, Train, AlertTriangle, CheckCircle2,
  ChevronRight, BarChart3, GitCompare, FileUp, FileDown
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';

interface GateConfig {
  gateId: string;
  name: string;
  openTime: string;
  closeTime: string;
  capacity: number;
}

interface ScenarioPlan {
  id: string;
  name: string;
  venue: string;
  attendance: number;
  eventStart: string;
  gatesOpen: string;
  gates: GateConfig[];
  transportMode: 'heavy' | 'moderate' | 'light';
  parkingCapacity: number;
  results?: SimulationResults;
}

interface SimulationResults {
  maxQueueLength: number;
  maxQueueTime: number;
  entryCompleteTime: string;
  riskZones: number;
  bottlenecks: string[];
  recommendations: string[];
  overallScore: number;
}

const defaultGates: GateConfig[] = [
  { gateId: 'gate-a', name: 'Gate A (North)', openTime: '18:00', closeTime: '19:45', capacity: 500 },
  { gateId: 'gate-b', name: 'Gate B (East)', openTime: '18:00', closeTime: '19:45', capacity: 400 },
  { gateId: 'gate-c', name: 'Gate C (South)', openTime: '18:30', closeTime: '19:45', capacity: 450 },
  { gateId: 'gate-d', name: 'Gate D (West)', openTime: '18:30', closeTime: '19:45', capacity: 350 },
];

const venues = [
  { id: 'bukit-jalil', name: 'Stadium Nasional Bukit Jalil', capacity: 87000 },
  { id: 'axiata-arena', name: 'Axiata Arena', capacity: 16000 },
  { id: 'merdeka-stadium', name: 'Stadium Merdeka', capacity: 25000 },
];

export default function PlannerPage() {
  const [scenarios, setScenarios] = useState<ScenarioPlan[]>([
    {
      id: 'scenario-1',
      name: 'Current Plan',
      venue: 'bukit-jalil',
      attendance: 70000,
      eventStart: '19:30',
      gatesOpen: '18:00',
      gates: [...defaultGates],
      transportMode: 'heavy',
      parkingCapacity: 15000,
    },
  ]);
  const [selectedScenario, setSelectedScenario] = useState<string>('scenario-1');
  const [isSimulating, setIsSimulating] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [importError, setImportError] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Export all scenarios to JSON file
  const exportPlan = () => {
    try {
      const exportData = {
        version: '1.0',
        exportedAt: new Date().toISOString(),
        scenarios: scenarios,
      };
      const json = JSON.stringify(exportData, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `crowd-control-plan-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  // Import scenarios from JSON file
  const importPlan = async (file: File) => {
    setImportError(null);
    try {
      const text = await file.text();
      const data = JSON.parse(text);

      if (!data.scenarios || !Array.isArray(data.scenarios)) {
        throw new Error('Invalid file format: missing scenarios array');
      }

      // Validate each scenario has required fields
      for (const scenario of data.scenarios) {
        if (!scenario.id || !scenario.name || !scenario.venue) {
          throw new Error('Invalid scenario: missing required fields (id, name, venue)');
        }
      }

      setScenarios(data.scenarios);
      setSelectedScenario(data.scenarios[0]?.id || 'scenario-1');
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Failed to import plan');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      importPlan(e.target.files[0]);
      e.target.value = ''; // Reset input
    }
  };

  const currentScenario = scenarios.find(s => s.id === selectedScenario);

  const addScenario = () => {
    const newId = `scenario-${scenarios.length + 1}`;
    setScenarios([
      ...scenarios,
      {
        id: newId,
        name: `Scenario ${scenarios.length + 1}`,
        venue: 'bukit-jalil',
        attendance: 70000,
        eventStart: '19:30',
        gatesOpen: '18:00',
        gates: [...defaultGates],
        transportMode: 'moderate',
        parkingCapacity: 15000,
      },
    ]);
    setSelectedScenario(newId);
  };

  const deleteScenario = (id: string) => {
    if (scenarios.length <= 1) return;
    const newScenarios = scenarios.filter(s => s.id !== id);
    setScenarios(newScenarios);
    if (selectedScenario === id) {
      setSelectedScenario(newScenarios[0].id);
    }
  };

  const updateScenario = (updates: Partial<ScenarioPlan>) => {
    setScenarios(scenarios.map(s =>
      s.id === selectedScenario ? { ...s, ...updates } : s
    ));
  };

  const updateGate = (gateId: string, updates: Partial<GateConfig>) => {
    if (!currentScenario) return;
    const updatedGates = currentScenario.gates.map(g =>
      g.gateId === gateId ? { ...g, ...updates } : g
    );
    updateScenario({ gates: updatedGates });
  };

  const runSimulation = async () => {
    setIsSimulating(true);

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Generate mock results based on scenario config
    const scenario = currentScenario!;
    const totalGateCapacity = scenario.gates.reduce((sum, g) => sum + g.capacity, 0);
    const entryRate = totalGateCapacity * 60; // per hour

    // Calculate metrics
    const earlyGates = scenario.gates.filter(g => g.openTime <= '18:00').length;
    const maxQueue = Math.max(1000, scenario.attendance / (earlyGates * 2) - entryRate / 4);
    const entryDuration = scenario.attendance / entryRate;
    const entryComplete = addMinutes(scenario.gatesOpen, Math.ceil(entryDuration * 60));

    const results: SimulationResults = {
      maxQueueLength: Math.round(maxQueue * (0.8 + Math.random() * 0.4)),
      maxQueueTime: Math.round((maxQueue / totalGateCapacity) * (0.9 + Math.random() * 0.2)),
      entryCompleteTime: entryComplete,
      riskZones: Math.max(0, Math.floor((scenario.attendance / 20000) - earlyGates + 1)),
      bottlenecks: generateBottlenecks(scenario),
      recommendations: generateRecommendations(scenario),
      overallScore: calculateScore(scenario, earlyGates),
    };

    updateScenario({ results });
    setIsSimulating(false);
  };

  const toggleCompare = (id: string) => {
    if (selectedForCompare.includes(id)) {
      setSelectedForCompare(selectedForCompare.filter(s => s !== id));
    } else if (selectedForCompare.length < 3) {
      setSelectedForCompare([...selectedForCompare, id]);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 hover:bg-muted rounded-lg transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-lg font-semibold">Pre-Event Planner</h1>
              <p className="text-sm text-muted-foreground">
                Plan and compare scenarios before the event
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={compareMode ? 'default' : 'outline'}
              size="sm"
              onClick={() => setCompareMode(!compareMode)}
            >
              <GitCompare className="w-4 h-4 mr-2" />
              Compare Mode
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleFileChange}
              className="hidden"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
            >
              <FileUp className="w-4 h-4 mr-2" />
              Import Plan
            </Button>
            <Button
              variant={exportSuccess ? 'default' : 'outline'}
              size="sm"
              onClick={exportPlan}
              className={exportSuccess ? 'bg-green-600 hover:bg-green-700' : ''}
            >
              {exportSuccess ? (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Exported!
                </>
              ) : (
                <>
                  <FileDown className="w-4 h-4 mr-2" />
                  Export Plan
                </>
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Import Error Banner */}
      {importError && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <div className="container flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">Import Failed:</span>
              <span className="text-sm">{importError}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setImportError(null)}
              className="text-red-700 hover:bg-red-100"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}

      <main className="container py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Scenario List - Left Sidebar */}
          <div className="lg:col-span-3 space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Scenarios</CardTitle>
                  <Button size="sm" variant="outline" onClick={addScenario}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {scenarios.map(scenario => (
                  <div
                    key={scenario.id}
                    onClick={() => !compareMode && setSelectedScenario(scenario.id)}
                    className={cn(
                      'p-3 rounded-lg border cursor-pointer transition-all',
                      selectedScenario === scenario.id && !compareMode
                        ? 'border-primary bg-primary/5'
                        : 'hover:bg-muted/50',
                      compareMode && selectedForCompare.includes(scenario.id)
                        && 'border-blue-500 bg-blue-50'
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">{scenario.name}</span>
                      {compareMode ? (
                        <input
                          type="checkbox"
                          checked={selectedForCompare.includes(scenario.id)}
                          onChange={() => toggleCompare(scenario.id)}
                          className="w-4 h-4"
                        />
                      ) : (
                        scenarios.length > 1 && (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteScenario(scenario.id);
                            }}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        )
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {scenario.attendance.toLocaleString()} attendees
                    </div>
                    {scenario.results && (
                      <div className="mt-2 flex items-center gap-2">
                        <Badge
                          variant={scenario.results.overallScore >= 80 ? 'default' :
                                  scenario.results.overallScore >= 60 ? 'secondary' : 'destructive'}
                          className="text-[10px]"
                        >
                          Score: {scenario.results.overallScore}
                        </Badge>
                        {scenario.results.riskZones > 0 && (
                          <Badge variant="outline" className="text-[10px]">
                            {scenario.results.riskZones} risks
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>

            {compareMode && selectedForCompare.length >= 2 && (
              <Button className="w-full" onClick={() => setCompareMode(false)}>
                <BarChart3 className="w-4 h-4 mr-2" />
                View Comparison
              </Button>
            )}
          </div>

          {/* Main Content */}
          <div className="lg:col-span-9">
            {compareMode && selectedForCompare.length >= 2 ? (
              <ComparisonView
                scenarios={scenarios.filter(s => selectedForCompare.includes(s.id))}
              />
            ) : currentScenario ? (
              <Tabs defaultValue="config" className="space-y-6">
                <TabsList>
                  <TabsTrigger value="config">Configuration</TabsTrigger>
                  <TabsTrigger value="gates">Gate Schedule</TabsTrigger>
                  <TabsTrigger value="transport">Transport</TabsTrigger>
                  <TabsTrigger value="results" disabled={!currentScenario.results}>
                    Results
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="config" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Event Configuration</CardTitle>
                      <CardDescription>
                        Set up the basic event parameters
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Scenario Name</Label>
                          <Input
                            value={currentScenario.name}
                            onChange={(e) => updateScenario({ name: e.target.value })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Venue</Label>
                          <Select
                            value={currentScenario.venue}
                            onValueChange={(v) => updateScenario({ venue: v })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {venues.map(v => (
                                <SelectItem key={v.id} value={v.id}>
                                  {v.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <Label>Expected Attendance</Label>
                          <span className="text-lg font-semibold">
                            {currentScenario.attendance.toLocaleString()}
                          </span>
                        </div>
                        <Slider
                          value={[currentScenario.attendance]}
                          onValueChange={([v]) => updateScenario({ attendance: v })}
                          min={10000}
                          max={100000}
                          step={1000}
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>10,000</span>
                          <span>100,000</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Gates Open</Label>
                          <Input
                            type="time"
                            value={currentScenario.gatesOpen}
                            onChange={(e) => updateScenario({ gatesOpen: e.target.value })}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Event Start</Label>
                          <Input
                            type="time"
                            value={currentScenario.eventStart}
                            onChange={(e) => updateScenario({ eventStart: e.target.value })}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="flex justify-end">
                    <Button onClick={runSimulation} disabled={isSimulating}>
                      {isSimulating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                          Simulating...
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Run Simulation
                        </>
                      )}
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="gates" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Gate Schedule</CardTitle>
                      <CardDescription>
                        Configure opening times and capacity for each gate
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {currentScenario.gates.map(gate => (
                          <div
                            key={gate.gateId}
                            className="flex items-center gap-4 p-4 border rounded-lg"
                          >
                            <div className="flex-1">
                              <div className="font-medium">{gate.name}</div>
                              <div className="text-sm text-muted-foreground">
                                {gate.capacity} people/min capacity
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="space-y-1">
                                <Label className="text-xs">Opens</Label>
                                <Input
                                  type="time"
                                  value={gate.openTime}
                                  onChange={(e) => updateGate(gate.gateId, { openTime: e.target.value })}
                                  className="w-28"
                                />
                              </div>
                              <ChevronRight className="w-4 h-4 text-muted-foreground" />
                              <div className="space-y-1">
                                <Label className="text-xs">Closes</Label>
                                <Input
                                  type="time"
                                  value={gate.closeTime}
                                  onChange={(e) => updateGate(gate.gateId, { closeTime: e.target.value })}
                                  className="w-28"
                                />
                              </div>
                            </div>
                            <div className="w-32 space-y-1">
                              <Label className="text-xs">Capacity/min</Label>
                              <Input
                                type="number"
                                value={gate.capacity}
                                onChange={(e) => updateGate(gate.gateId, { capacity: parseInt(e.target.value) || 0 })}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="transport" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Transport Configuration</CardTitle>
                      <CardDescription>
                        Set expected transport patterns for the event
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="space-y-4">
                        <Label>Public Transport Usage</Label>
                        <div className="grid grid-cols-3 gap-4">
                          {(['heavy', 'moderate', 'light'] as const).map(mode => (
                            <Card
                              key={mode}
                              className={cn(
                                'cursor-pointer transition-all',
                                currentScenario.transportMode === mode
                                  ? 'border-primary bg-primary/5'
                                  : 'hover:bg-muted/50'
                              )}
                              onClick={() => updateScenario({ transportMode: mode })}
                            >
                              <CardContent className="p-4 text-center">
                                <Train className={cn(
                                  'w-8 h-8 mx-auto mb-2',
                                  currentScenario.transportMode === mode
                                    ? 'text-primary'
                                    : 'text-muted-foreground'
                                )} />
                                <div className="font-medium capitalize">{mode}</div>
                                <div className="text-xs text-muted-foreground">
                                  {mode === 'heavy' ? '70% LRT/Bus' :
                                   mode === 'moderate' ? '50% LRT/Bus' : '30% LRT/Bus'}
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <Label>Parking Capacity</Label>
                          <span className="font-medium">
                            {currentScenario.parkingCapacity.toLocaleString()} vehicles
                          </span>
                        </div>
                        <Slider
                          value={[currentScenario.parkingCapacity]}
                          onValueChange={([v]) => updateScenario({ parkingCapacity: v })}
                          min={5000}
                          max={30000}
                          step={500}
                        />
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="results" className="space-y-6">
                  {currentScenario.results && (
                    <ResultsView results={currentScenario.results} />
                  )}
                </TabsContent>
              </Tabs>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}

function ResultsView({ results }: { results: SimulationResults }) {
  return (
    <div className="space-y-6">
      {/* Score Card */}
      <Card className={cn(
        'border-2',
        results.overallScore >= 80 ? 'border-green-500 bg-green-50' :
        results.overallScore >= 60 ? 'border-yellow-500 bg-yellow-50' :
        'border-red-500 bg-red-50'
      )}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-muted-foreground mb-1">Overall Score</div>
              <div className="text-4xl font-bold">{results.overallScore}/100</div>
              <div className="text-sm mt-1">
                {results.overallScore >= 80 ? 'Good plan - minor optimizations possible' :
                 results.overallScore >= 60 ? 'Acceptable - some improvements recommended' :
                 'Needs improvement - significant risks detected'}
              </div>
            </div>
            <div className={cn(
              'w-20 h-20 rounded-full flex items-center justify-center',
              results.overallScore >= 80 ? 'bg-green-500' :
              results.overallScore >= 60 ? 'bg-yellow-500' :
              'bg-red-500'
            )}>
              {results.overallScore >= 80 ? (
                <CheckCircle2 className="w-10 h-10 text-white" />
              ) : (
                <AlertTriangle className="w-10 h-10 text-white" />
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Users className="w-4 h-4" />
              <span className="text-xs">Max Queue</span>
            </div>
            <div className="text-2xl font-semibold">
              {results.maxQueueLength.toLocaleString()}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Clock className="w-4 h-4" />
              <span className="text-xs">Max Wait</span>
            </div>
            <div className="text-2xl font-semibold">
              {results.maxQueueTime} min
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <CheckCircle2 className="w-4 h-4" />
              <span className="text-xs">Entry Complete</span>
            </div>
            <div className="text-2xl font-semibold">
              {results.entryCompleteTime}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-xs">Risk Zones</span>
            </div>
            <div className="text-2xl font-semibold">
              {results.riskZones}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottlenecks */}
      {results.bottlenecks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              Predicted Bottlenecks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {results.bottlenecks.map((b, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="w-5 h-5 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-xs flex-shrink-0">
                    {i + 1}
                  </span>
                  {b}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {results.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs flex-shrink-0">
                  {i + 1}
                </span>
                {r}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

function ComparisonView({ scenarios }: { scenarios: ScenarioPlan[] }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Scenario Comparison</CardTitle>
          <CardDescription>
            Side-by-side analysis of {scenarios.length} scenarios
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium">Metric</th>
                  {scenarios.map(s => (
                    <th key={s.id} className="text-center py-3 px-4 font-medium">
                      {s.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="py-3 px-4 text-muted-foreground">Attendance</td>
                  {scenarios.map(s => (
                    <td key={s.id} className="py-3 px-4 text-center font-medium">
                      {s.attendance.toLocaleString()}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-muted-foreground">Gates Open</td>
                  {scenarios.map(s => (
                    <td key={s.id} className="py-3 px-4 text-center">
                      {s.gatesOpen}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-muted-foreground">Overall Score</td>
                  {scenarios.map(s => (
                    <td key={s.id} className="py-3 px-4 text-center">
                      {s.results ? (
                        <Badge
                          variant={s.results.overallScore >= 80 ? 'default' :
                                  s.results.overallScore >= 60 ? 'secondary' : 'destructive'}
                        >
                          {s.results.overallScore}/100
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">Not simulated</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-muted-foreground">Max Queue</td>
                  {scenarios.map(s => (
                    <td key={s.id} className="py-3 px-4 text-center">
                      {s.results ? s.results.maxQueueLength.toLocaleString() : '-'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-muted-foreground">Max Wait Time</td>
                  {scenarios.map(s => (
                    <td key={s.id} className="py-3 px-4 text-center">
                      {s.results ? `${s.results.maxQueueTime} min` : '-'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-muted-foreground">Entry Complete</td>
                  {scenarios.map(s => (
                    <td key={s.id} className="py-3 px-4 text-center">
                      {s.results?.entryCompleteTime || '-'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-muted-foreground">Risk Zones</td>
                  {scenarios.map(s => (
                    <td key={s.id} className="py-3 px-4 text-center">
                      {s.results ? (
                        <span className={cn(
                          s.results.riskZones === 0 ? 'text-green-600' :
                          s.results.riskZones <= 2 ? 'text-yellow-600' : 'text-red-600'
                        )}>
                          {s.results.riskZones}
                        </span>
                      ) : '-'}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Best Scenario Highlight */}
      {scenarios.every(s => s.results) && (
        <Card className="border-green-500 bg-green-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
              <div>
                <div className="font-medium">Recommended: {
                  scenarios.reduce((best, s) =>
                    (s.results?.overallScore || 0) > (best.results?.overallScore || 0) ? s : best
                  ).name
                }</div>
                <div className="text-sm text-muted-foreground">
                  This scenario has the highest overall score and fewest risk zones
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Helper functions
function addMinutes(time: string, minutes: number): string {
  const [h, m] = time.split(':').map(Number);
  const totalMins = h * 60 + m + minutes;
  const newH = Math.floor(totalMins / 60) % 24;
  const newM = totalMins % 60;
  return `${newH.toString().padStart(2, '0')}:${newM.toString().padStart(2, '0')}`;
}

function generateBottlenecks(scenario: ScenarioPlan): string[] {
  const bottlenecks: string[] = [];
  const earlyGates = scenario.gates.filter(g => g.openTime <= '18:00');

  if (earlyGates.length < 2) {
    bottlenecks.push('Only ' + earlyGates.length + ' gate(s) open at start - expect heavy queuing at Gate A');
  }

  if (scenario.attendance > 60000 && scenario.transportMode === 'heavy') {
    bottlenecks.push('LRT arrival surge expected at 18:30-18:45 - congestion at Gate B near LRT exit');
  }

  if (scenario.parkingCapacity < scenario.attendance * 0.3) {
    bottlenecks.push('Parking overflow predicted at 18:15 - redirect to alternate lots');
  }

  const lateGates = scenario.gates.filter(g => g.openTime >= '18:30');
  if (lateGates.length > 0) {
    bottlenecks.push(`${lateGates.map(g => g.name.split(' ')[0] + ' ' + g.name.split(' ')[1]).join(', ')} opening late may cause imbalanced crowd distribution`);
  }

  return bottlenecks;
}

function generateRecommendations(scenario: ScenarioPlan): string[] {
  const recs: string[] = [];
  const earlyGates = scenario.gates.filter(g => g.openTime <= '18:00');

  if (earlyGates.length < scenario.gates.length) {
    recs.push('Open all gates at 18:00 to distribute crowd evenly');
  }

  if (scenario.transportMode === 'heavy') {
    recs.push('Deploy additional staff at Gate B (LRT exit) between 18:30-19:00');
  }

  recs.push('Announce entry by zone: North Stand first, then South Stand after 15 min');

  if (scenario.attendance > 50000) {
    recs.push('Activate all restroom facilities 30 minutes before gates open');
  }

  recs.push('Prepare traffic controllers at Jalan Besar junction for parking overflow');

  return recs;
}

function calculateScore(scenario: ScenarioPlan, earlyGates: number): number {
  let score = 100;

  // Penalize for late gate openings
  if (earlyGates < scenario.gates.length) {
    score -= (scenario.gates.length - earlyGates) * 10;
  }

  // Penalize for high attendance without enough parking
  if (scenario.parkingCapacity < scenario.attendance * 0.25) {
    score -= 15;
  }

  // Penalize for heavy transport without preparation time
  if (scenario.transportMode === 'heavy' && scenario.gatesOpen > '18:00') {
    score -= 10;
  }

  // Penalize for very high attendance
  if (scenario.attendance > 80000) {
    score -= 10;
  }

  // Add randomness for realism
  score += Math.floor(Math.random() * 10) - 5;

  return Math.max(30, Math.min(95, score));
}
