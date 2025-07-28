import React, { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Copy, Download, ExternalLink, AlertCircle, CheckCircle, Brain, Clock, User, Calendar, Upload, Link, Type, Zap } from 'lucide-react';
import { ApiService } from '@/fastapi_client';

interface CategoryResult {
  category_name: string;
  values: string[];
  confidence: number;
  evidence_text: string[];
  model_used: string;
}

interface AnalysisResult {
  customer_name?: string;
  meeting_date?: string;
  categories: Record<string, CategoryResult>;
  processing_time_ms: number;
  word_count: number;
}

interface TextAnalysisProps {
  selectedSchemaId?: string;
  onResultsChange?: (results: AnalysisResult | null) => void;
}

const TextAnalysis: React.FC<TextAnalysisProps> = ({ selectedSchemaId, onResultsChange }) => {
  const [inputText, setInputText] = useState('');
  const [googleDriveUrl, setGoogleDriveUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [inputType, setInputType] = useState<'text' | 'file' | 'url'>('text');
  const [fastMode, setFastMode] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async (data: { text?: string; google_drive_url?: string; file?: File; schema_template_id: string; extract_customer_info: boolean; fast_mode: boolean }) => {
      const formData = new FormData();
      formData.append('schema_template_id', data.schema_template_id);
      formData.append('extract_customer_info', data.extract_customer_info.toString());
      formData.append('fast_mode', data.fast_mode.toString());
      
      if (data.text) {
        formData.append('text', data.text);
      } else if (data.google_drive_url) {
        formData.append('google_drive_url', data.google_drive_url);
      } else if (data.file) {
        formData.append('file', data.file);
      }
      
      const response = await fetch('/api/insights/analyze-document', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Analysis failed');
      }
      
      return await response.json() as AnalysisResult;
    },
    onSuccess: (result) => {
      setAnalysisResult(result);
      onResultsChange?.(result);
    },
    onError: (error) => {
      console.error('Analysis failed:', error);
      setAnalysisResult(null);
      onResultsChange?.(null);
    }
  });

  const handleAnalyze = () => {
    if (!selectedSchemaId) return;
    
    const hasInput = inputType === 'text' ? inputText.trim() : 
                    inputType === 'url' ? googleDriveUrl.trim() : 
                    inputType === 'file' ? selectedFile : false;
    
    if (!hasInput) return;

    analysisMutation.mutate({
      text: inputType === 'text' ? inputText : undefined,
      google_drive_url: inputType === 'url' ? googleDriveUrl : undefined,
      file: inputType === 'file' ? selectedFile! : undefined,
      schema_template_id: selectedSchemaId,
      extract_customer_info: true,
      fast_mode: fastMode
    });
  };

  const handleClear = () => {
    setInputText('');
    setGoogleDriveUrl('');
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setAnalysisResult(null);
    onResultsChange?.(null);
  };
  
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportToCsv = () => {
    if (!analysisResult) return;

    // Create CSV header
    const headers = ['Customer', 'Meeting Date'];
    const categoryNames = Object.keys(analysisResult.categories);
    headers.push(...categoryNames);

    // Create CSV row
    const row = [
      analysisResult.customer_name || '',
      analysisResult.meeting_date || ''
    ];

    categoryNames.forEach(categoryName => {
      const category = analysisResult.categories[categoryName];
      row.push(category.values.join(', '));
    });

    // Combine into CSV
    const csvContent = [headers.join(','), row.join(',')].join('\n');
    
    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `customer-insights-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const createGoogleSheetsFormula = () => {
    if (!analysisResult) return '';

    const headers = ['Customer', 'Meeting Date'];
    const categoryNames = Object.keys(analysisResult.categories);
    headers.push(...categoryNames);

    const row = [
      analysisResult.customer_name || '',
      analysisResult.meeting_date || ''
    ];

    categoryNames.forEach(categoryName => {
      const category = analysisResult.categories[categoryName];
      row.push(category.values.join(', '));
    });

    return row.join('\t'); // Tab-separated for easy pasting
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Document Analysis
          </CardTitle>
          <CardDescription>
            Choose your input method and analyze customer documents for instant insights
            {!selectedSchemaId && (
              <span className="text-red-600 ml-2">→ Please select a schema first</span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Input Type Tabs */}
          <Tabs value={inputType} onValueChange={(value) => setInputType(value as 'text' | 'file' | 'url')}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="text" className="flex items-center gap-2">
                <Type className="h-4 w-4" />
                Text Input
              </TabsTrigger>
              <TabsTrigger value="file" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                File Upload
              </TabsTrigger>
              <TabsTrigger value="url" className="flex items-center gap-2">
                <Link className="h-4 w-4" />
                Google Drive
              </TabsTrigger>
            </TabsList>
            
            {/* Text Input */}
            <TabsContent value="text" className="space-y-4">
              <Textarea
                placeholder="Paste your customer meeting notes here...&#10;&#10;Example:&#10;Meeting with Acme Corp on March 15, 2024&#10;&#10;Discussion about implementing vector search for their retail platform.&#10;Currently using basic keyword search but want semantic capabilities.&#10;Need both batch processing for catalog updates and real-time search.&#10;Timeline: Q2 2024"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                rows={8}
                className="min-h-[200px]"
              />
              <div className="text-sm text-gray-600">
                {inputText.split(/\s+/).filter(word => word.length > 0).length} words
              </div>
            </TabsContent>
            
            {/* File Upload */}
            <TabsContent value="file" className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <div className="space-y-2">
                  <p className="text-sm font-medium">Upload a document</p>
                  <p className="text-xs text-gray-500">Supports .txt and .docx files up to 10MB</p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.docx"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <Button 
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="mt-4"
                >
                  Choose File
                </Button>
                {selectedFile && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-800">
                      Selected: {selectedFile.name}
                    </p>
                    <p className="text-xs text-blue-600">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>
            
            {/* Google Drive URL */}
            <TabsContent value="url" className="space-y-4">
              <div className="space-y-3">
                <Input
                  placeholder="https://docs.google.com/document/d/your-document-id/edit"
                  value={googleDriveUrl}
                  onChange={(e) => setGoogleDriveUrl(e.target.value)}
                  className=""
                />
                <div className="text-sm text-gray-600">
                  <p>• Paste a Google Docs share link</p>
                  <p>• Make sure the document is publicly viewable or shared with your account</p>
                  <p className="text-amber-600 mt-2">⚠️ Full Google Drive integration requires OAuth setup in production</p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
          
          {/* Fast Mode Toggle */}
          <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={fastMode}
                onChange={(e) => setFastMode(e.target.checked)}
                className="rounded"
              />
              <Zap className="h-4 w-4 text-amber-600" />
              <span className="text-sm font-medium text-amber-800">Fast Mode</span>
            </label>
            <div className="text-xs text-amber-700 flex-1">
              Use when AI processing is slow or rate limited. Uses keyword matching instead of AI analysis.
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Input type: {inputType === 'text' ? 'Direct text' : inputType === 'file' ? 'File upload' : 'Google Drive URL'}
              {fastMode && <span className="text-amber-600 ml-2">• Fast mode enabled</span>}
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={handleClear}
                disabled={!inputText && !selectedFile && !googleDriveUrl && !analysisResult}
              >
                Clear
              </Button>
              <Button 
                onClick={handleAnalyze}
                disabled={!selectedSchemaId || analysisMutation.isPending || 
                  (inputType === 'text' && !inputText.trim()) ||
                  (inputType === 'file' && !selectedFile) ||
                  (inputType === 'url' && !googleDriveUrl.trim())
                }
              >
                {analysisMutation.isPending ? (
                  <>
                    <Brain className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4 mr-2" />
                    Analyze Document
                  </>
                )}
              </Button>
            </div>
          </div>

          {analysisMutation.isPending && (
            <div className="space-y-2">
              <Progress value={66} className="w-full" />
              <p className="text-sm text-gray-600 text-center">
                AI is extracting insights from your text...
              </p>
            </div>
          )}

          {analysisMutation.isError && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Failed to analyze document. Please check your input and schema selection, then try again.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results Section */}
      {analysisResult && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Analysis Results
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(createGoogleSheetsFormula())}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy for Sheets
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={exportToCsv}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            </div>
            <CardDescription className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {analysisResult.processing_time_ms}ms
              </span>
              <span className="flex items-center gap-1">
                <Brain className="h-4 w-4" />
                {Object.keys(analysisResult.categories).length} categories
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Customer Information */}
            {(analysisResult.customer_name || analysisResult.meeting_date) && (
              <div className="grid md:grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg">
                {analysisResult.customer_name && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-blue-600" />
                    <span className="font-medium">Customer:</span>
                    <span>{analysisResult.customer_name}</span>
                  </div>
                )}
                {analysisResult.meeting_date && (
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-blue-600" />
                    <span className="font-medium">Meeting Date:</span>
                    <span>{analysisResult.meeting_date}</span>
                  </div>
                )}
              </div>
            )}

            {/* Category Results */}
            <div className="space-y-4">
              <h4 className="font-semibold">Extracted Categories</h4>
              <div className="grid gap-4">
                {Object.entries(analysisResult.categories).map(([categoryName, category]) => (
                  <Card key={categoryName} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium">{categoryName}</h5>
                        <Badge className={getConfidenceColor(category.confidence)}>
                          {getConfidenceLabel(category.confidence)} ({Math.round(category.confidence * 100)}%)
                        </Badge>
                      </div>
                      
                      {category.values.length > 0 ? (
                        <div className="space-y-2">
                          <div className="flex flex-wrap gap-1">
                            {category.values.map((value, i) => (
                              <Badge key={i} variant="default">
                                {value}
                              </Badge>
                            ))}
                          </div>
                          
                          {category.evidence_text.length > 0 && (
                            <details className="mt-2">
                              <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-800">
                                View supporting evidence
                              </summary>
                              <div className="mt-2 space-y-1">
                                {category.evidence_text.map((evidence, i) => (
                                  <p key={i} className="text-sm text-gray-700 italic p-2 bg-gray-50 rounded">
                                    "{evidence.trim()}"
                                  </p>
                                ))}
                              </div>
                            </details>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500 italic">
                          No clear match found in the text
                        </p>
                      )}
                      
                      <div className="mt-2 text-xs text-gray-500">
                        Model: {category.model_used}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Export Preview */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h5 className="font-medium mb-2">Google Sheets Preview</h5>
              <div className="font-mono text-sm bg-white p-3 rounded border overflow-x-auto">
                <div className="grid grid-cols-1 gap-1">
                  <div className="font-semibold text-gray-600">
                    Customer | Meeting Date | {Object.keys(analysisResult.categories).join(' | ')}
                  </div>
                  <div>
                    {analysisResult.customer_name || '(not found)'} | {analysisResult.meeting_date || '(not found)'} | {
                      Object.values(analysisResult.categories)
                        .map(cat => cat.values.join(', ') || '(none)')
                        .join(' | ')
                    }
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-600 mt-2">
                Use "Copy for Sheets" to copy this data in tab-separated format for pasting into Google Sheets
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TextAnalysis;