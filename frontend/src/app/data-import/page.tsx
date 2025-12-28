'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Upload, FileText, Download, CheckCircle2,
  AlertCircle, Loader2, Ticket, Train, Calendar
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';

interface ImportResult {
  success: boolean;
  records_imported: number;
  errors: string[];
  summary: Record<string, unknown>;
}

interface Toast {
  id: string;
  type: 'success' | 'error';
  message: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DataImportPage() {
  const [activeTab, setActiveTab] = useState('ticketing');
  const [eventId, setEventId] = useState('my-event');
  const [isUploading, setIsUploading] = useState(false);
  const [isDownloading, setIsDownloading] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (type: 'success' | 'error', message: string) => {
    const id = Math.random().toString(36).substring(7);
    setToasts(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  }, [activeTab]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/api/data/upload/${activeTab}?event_id=${encodeURIComponent(eventId)}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        records_imported: 0,
        errors: [error instanceof Error ? error.message : 'Upload failed'],
        summary: {},
      });
    } finally {
      setIsUploading(false);
    }
  };

  const downloadTemplate = async (type: string) => {
    setIsDownloading(`template-${type}`);
    try {
      const response = await fetch(`${API_BASE}/api/data/templates/${type}`);

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.csv_content) {
        throw new Error('Invalid response: missing csv_content');
      }

      const blob = new Blob([data.csv_content], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}_template.csv`;
      a.click();
      URL.revokeObjectURL(url);
      showToast('success', `Template downloaded: ${type}_template.csv`);
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to download template';
      showToast('error', msg);
      console.error('Failed to download template:', error);
    } finally {
      setIsDownloading(null);
    }
  };

  const generateSampleData = async (type: string) => {
    setIsDownloading(`sample-${type}`);
    try {
      const response = await fetch(`${API_BASE}/api/data/sample/${type}?count=100`);

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Convert to CSV and trigger download
      if (data.data && data.data.length > 0) {
        const headers = Object.keys(data.data[0]).join(',');
        const rows = data.data.map((row: Record<string, unknown>) =>
          Object.values(row).join(',')
        ).join('\n');
        const csv = `${headers}\n${rows}`;

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${type}_sample_data.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('success', `Generated ${data.count} sample records`);
      } else {
        throw new Error('No data returned from server');
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Failed to generate sample data';
      showToast('error', msg);
      console.error('Failed to generate sample:', error);
    } finally {
      setIsDownloading(null);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Toast Notifications */}
      <div className="fixed top-4 right-4 z-[100] space-y-2">
        {toasts.map(toast => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            className={cn(
              'px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 min-w-[250px]',
              toast.type === 'success'
                ? 'bg-green-600 text-white'
                : 'bg-red-600 text-white'
            )}
          >
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            <span className="text-sm font-medium">{toast.message}</span>
          </motion.div>
        ))}
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 hover:bg-muted rounded-lg transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-lg font-semibold">Data Import</h1>
              <p className="text-sm text-muted-foreground">
                Upload ticketing, transport, and schedule data
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="container py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Info Card */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-medium text-blue-900">No Hardware Required</p>
                  <p className="text-sm text-blue-700">
                    Upload your existing ticketing data, transport schedules, and event configurations.
                    The system uses this data to simulate crowd movements without any IoT sensors.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Import Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="ticketing" className="gap-2">
                <Ticket className="w-4 h-4" />
                Ticketing
              </TabsTrigger>
              <TabsTrigger value="transport" className="gap-2">
                <Train className="w-4 h-4" />
                Transport
              </TabsTrigger>
              <TabsTrigger value="schedule" className="gap-2">
                <Calendar className="w-4 h-4" />
                Schedule
              </TabsTrigger>
            </TabsList>

            <TabsContent value="ticketing" className="space-y-6">
              <DataTypeInfo
                title="Ticketing Data"
                description="Upload ticket sales data including zones, gates, and estimated entry times."
                columns={['ticket_id', 'zone', 'gate', 'purchase_time', 'entry_time_estimate', 'seat_section']}
                onDownloadTemplate={() => downloadTemplate('ticketing')}
                onGenerateSample={() => generateSampleData('ticketing')}
                isDownloadingTemplate={isDownloading === 'template-ticketing'}
                isGeneratingSample={isDownloading === 'sample-ticketing'}
              />
            </TabsContent>

            <TabsContent value="transport" className="space-y-6">
              <DataTypeInfo
                title="Transport Schedule"
                description="Upload LRT/bus arrival times and expected passenger counts."
                columns={['transport_type', 'station', 'arrival_time', 'capacity', 'expected_passengers']}
                onDownloadTemplate={() => downloadTemplate('transport')}
                onGenerateSample={() => generateSampleData('transport')}
                isDownloadingTemplate={isDownloading === 'template-transport'}
                isGeneratingSample={isDownloading === 'sample-transport'}
              />
            </TabsContent>

            <TabsContent value="schedule" className="space-y-6">
              <DataTypeInfo
                title="Event Schedule"
                description="Upload event phases including gates open, halftime, and exit periods."
                columns={['event_phase', 'start_time', 'end_time', 'description']}
                onDownloadTemplate={() => downloadTemplate('schedule')}
                onGenerateSample={() => generateSampleData('schedule')}
                isDownloadingTemplate={isDownloading === 'template-schedule'}
                isGeneratingSample={isDownloading === 'sample-schedule'}
              />
            </TabsContent>
          </Tabs>

          {/* Event ID Input */}
          <Card>
            <CardHeader>
              <CardTitle>Event Configuration</CardTitle>
              <CardDescription>
                Set an event ID to group your uploaded data and create a custom scenario
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="event-id">Event ID</Label>
                <Input
                  id="event-id"
                  value={eventId}
                  onChange={(e) => setEventId(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
                  placeholder="my-custom-event"
                  className="max-w-sm"
                />
                <p className="text-xs text-muted-foreground">
                  Upload ticketing data to automatically create a runnable scenario
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Upload Zone */}
          <Card>
            <CardHeader>
              <CardTitle>Upload File</CardTitle>
              <CardDescription>
                Drag and drop a CSV or JSON file, or click to browse
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={cn(
                  'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
                  dragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25',
                  isUploading && 'opacity-50 pointer-events-none'
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept=".csv,.json"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                  disabled={isUploading}
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  {isUploading ? (
                    <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                  ) : (
                    <Upload className="w-12 h-12 text-muted-foreground mb-4" />
                  )}
                  <p className="text-lg font-medium mb-1">
                    {isUploading ? 'Uploading...' : 'Drop your file here'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Supports CSV and JSON formats
                  </p>
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card className={cn(
                'border-2',
                result.success ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
              )}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {result.success ? (
                      <>
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                        <span className="text-green-800">Import Successful</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-5 h-5 text-red-600" />
                        <span className="text-red-800">Import Failed</span>
                      </>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Records Imported</p>
                      <p className="text-2xl font-semibold">{result.records_imported}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Errors</p>
                      <p className="text-2xl font-semibold">{result.errors.length}</p>
                    </div>
                  </div>

                  {result.summary?.scenario_created && (
                    <div className="border-t pt-4">
                      <div className="flex items-center gap-2 mb-3">
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                        <span className="font-medium text-green-800">Custom Scenario Created!</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        Your uploaded data has been used to create a new runnable scenario.
                      </p>
                      <Link href={`/dashboard/${result.summary.scenario_id}`}>
                        <Button variant="default" size="sm">
                          Run Simulation →
                        </Button>
                      </Link>
                    </div>
                  )}

                  {result.summary && Object.keys(result.summary).length > 0 && (
                    <div className="border-t pt-4">
                      <p className="font-medium mb-2">Summary</p>
                      <div className="bg-white/50 rounded-lg p-3 text-sm">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(result.summary, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {result.errors.length > 0 && (
                    <div className="border-t pt-4">
                      <p className="font-medium mb-2 text-red-700">Errors</p>
                      <ul className="space-y-1">
                        {result.errors.map((error, i) => (
                          <li key={i} className="text-sm text-red-600">
                            {error}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </main>
    </div>
  );
}

function DataTypeInfo({
  title,
  description,
  columns,
  onDownloadTemplate,
  onGenerateSample,
  isDownloadingTemplate,
  isGeneratingSample,
}: {
  title: string;
  description: string;
  columns: string[];
  onDownloadTemplate: () => void;
  onGenerateSample?: () => void;
  isDownloadingTemplate?: boolean;
  isGeneratingSample?: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm font-medium mb-2">Expected Columns</p>
          <div className="flex flex-wrap gap-2">
            {columns.map(col => (
              <Badge key={col} variant="outline">
                {col}
              </Badge>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onDownloadTemplate}
            disabled={isDownloadingTemplate}
          >
            {isDownloadingTemplate ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            {isDownloadingTemplate ? 'Downloading...' : 'Download Template'}
          </Button>
          {onGenerateSample && (
            <Button
              variant="outline"
              size="sm"
              onClick={onGenerateSample}
              disabled={isGeneratingSample}
            >
              {isGeneratingSample ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <FileText className="w-4 h-4 mr-2" />
              )}
              {isGeneratingSample ? 'Generating...' : 'Generate Sample Data'}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
