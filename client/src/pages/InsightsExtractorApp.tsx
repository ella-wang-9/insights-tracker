import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { FileText, Brain, Database, BarChart3, Settings, FileSpreadsheet } from 'lucide-react';
import SchemaBuilder from '@/components/insights/SchemaBuilder';
import BatchAnalysis from '@/components/insights/BatchAnalysis';

// Create a query client for React Query
const queryClient = new QueryClient();

const InsightsExtractorApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState('schema'); // Start with schema tab
  const [selectedSchemaId, setSelectedSchemaId] = useState<string | undefined>();
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  const handleSchemaSelected = (templateId: string) => {
    setSelectedSchemaId(templateId);
    // Auto-switch to batch tab when schema is selected
    if (activeTab === 'schema') {
      setActiveTab('batch');
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Customer Insights Extractor</h1>
              <p className="text-gray-600">Transform customer meeting notes into structured insights</p>
            </div>
          </div>
          
          <div className="flex gap-4 flex-wrap">
            <Badge variant="secondary" className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              Document Processing
            </Badge>
            <Badge variant="secondary" className="flex items-center gap-1">
              <Brain className="h-3 w-3" />
              AI Categorization
            </Badge>
            <Badge variant="secondary" className="flex items-center gap-1">
              <Database className="h-3 w-3" />
              Delta Tables
            </Badge>
            <Badge variant="secondary" className="flex items-center gap-1">
              <BarChart3 className="h-3 w-3" />
              Analytics
            </Badge>
          </div>
        </div>

        {/* Main Interface */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="schema" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              1. Schema Builder
            </TabsTrigger>
            <TabsTrigger 
              value="batch" 
              className="flex items-center gap-2"
              disabled={!selectedSchemaId}
            >
              <FileSpreadsheet className="h-4 w-4" />
              2. Batch Process
            </TabsTrigger>
            <TabsTrigger 
              value="results" 
              className="flex items-center gap-2"
              disabled={!analysisResults}
            >
              <FileText className="h-4 w-4" />
              3. Results
            </TabsTrigger>
            <TabsTrigger 
              value="analytics" 
              className="flex items-center gap-2"
              disabled={!analysisResults}
            >
              <BarChart3 className="h-4 w-4" />
              4. Analytics
            </TabsTrigger>
          </TabsList>

          {/* Schema Builder Tab - FIRST */}
          <TabsContent value="schema" className="space-y-6">
            <SchemaBuilder 
              onSchemaSelected={handleSchemaSelected}
              selectedSchemaId={selectedSchemaId}
            />
          </TabsContent>

          {/* Batch Processing Tab - SECOND */}
          <TabsContent value="batch" className="space-y-6">
            {!selectedSchemaId && (
              <Card className="border-amber-200 bg-amber-50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-amber-800">
                    <Settings className="h-5 w-5" />
                    <span className="font-medium">Schema Required</span>
                  </div>
                  <p className="text-amber-700 mt-1">
                    Please select or create a schema template first to define what insights to extract.
                  </p>
                  <Button 
                    className="mt-3" 
                    size="sm" 
                    onClick={() => setActiveTab('schema')}
                  >
                    Go to Schema Builder
                  </Button>
                </CardContent>
              </Card>
            )}
            
            <BatchAnalysis selectedSchemaId={selectedSchemaId} />
          </TabsContent>

          {/* Results Tab */}
          <TabsContent value="results" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Analysis Results
                </CardTitle>
                <CardDescription>
                  View and export your structured customer insights
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 mb-4">
                  <Button variant="outline" size="sm">
                    Export to CSV
                  </Button>
                  <Button variant="outline" size="sm">
                    Copy for Google Sheets
                  </Button>
                  <Button variant="outline" size="sm">
                    Share Analysis
                  </Button>
                </div>

                <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center text-gray-500">
                  <BarChart3 className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                  <p className="mb-2">No analysis results yet</p>
                  <p className="text-sm">Process documents with a defined schema to see extracted insights here</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Executive Dashboard
                </CardTitle>
                <CardDescription>
                  High-level insights and trends from your customer feedback analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <Card className="border-dashed border-2">
                    <CardContent className="p-6 text-center">
                      <BarChart3 className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                      <h4 className="font-semibold">Cross-Category Insights</h4>
                      <p className="text-sm text-gray-600 mt-1">Coming soon</p>
                    </CardContent>
                  </Card>

                  <Card className="border-dashed border-2">
                    <CardContent className="p-6 text-center">
                      <BarChart3 className="h-8 w-8 text-green-600 mx-auto mb-2" />
                      <h4 className="font-semibold">Trend Analysis</h4>
                      <p className="text-sm text-gray-600 mt-1">Coming soon</p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
    </QueryClientProvider>
  );
};

export default InsightsExtractorApp;