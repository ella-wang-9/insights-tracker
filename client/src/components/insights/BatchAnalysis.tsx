import React, { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

// TypeScript declaration for webkitdirectory attribute
declare module 'react' {
  interface InputHTMLAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    webkitdirectory?: string;
  }
}
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Copy, Download, AlertCircle, Plus, X, FileText, Link, Type, Upload, FileSpreadsheet, Loader2, Table, FolderOpen } from 'lucide-react';

interface BatchInput {
  id: string;
  type: 'text' | 'file' | 'url' | 'folder';
  content: string;
  file?: File;
  files?: File[]; // For folder uploads
  filename?: string;
  filenames?: string[]; // For folder uploads
}

interface BatchAnalysisProps {
  selectedSchemaId?: string;
}

const BatchAnalysis: React.FC<BatchAnalysisProps> = ({ selectedSchemaId }) => {
  const [inputs, setInputs] = useState<BatchInput[]>([
    { id: '1', type: 'text', content: '' }
  ]);
  const [exportFormat, setExportFormat] = useState<'csv' | 'xlsx' | 'preview'>('preview');
  const [showResults, setShowResults] = useState(false);
  const [resultsData, setResultsData] = useState<any[]>([]);
  const fileInputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({});

  // Batch analysis mutation for files with preview
  const batchFilesMutation = useMutation({
    mutationFn: async (data: { files: File[]; schema_template_id: string; export_format: string }) => {
      const formData = new FormData();
      data.files.forEach(file => {
        formData.append('files', file);
      });
      formData.append('schema_template_id', data.schema_template_id);
      formData.append('export_format', isPreviewOnly ? 'xlsx' : data.export_format);
      if (isPreviewOnly) {
        formData.append('preview_only', 'true');
      }

      const response = await fetch('/api/batch/analyze-files-with-preview', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Batch analysis failed');
      }

      const result = await response.json();
      
      // Store results for display
      setResultsData(result.table_data);
      setShowResults(true);
      
      // Also create download link from base64
      const byteCharacters = atob(result.spreadsheet_base64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { 
        type: data.export_format === 'xlsx' 
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
          : 'text/csv' 
      });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      return result;
    }
  });

  // Batch analysis mutation for texts and URLs with preview
  const batchMixedMutation = useMutation({
    mutationFn: async (data: { texts: string[]; urls: string[]; schema_template_id: string; export_format: string }) => {
      const formData = new FormData();
      formData.append('schema_template_id', data.schema_template_id);
      formData.append('texts', JSON.stringify(data.texts));
      formData.append('urls', JSON.stringify(data.urls));
      formData.append('export_format', isPreviewOnly ? 'xlsx' : data.export_format);
      if (isPreviewOnly) {
        formData.append('preview_only', 'true');
      }

      const response = await fetch('/api/batch/analyze-with-preview', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Batch analysis failed');
      }

      const result = await response.json();
      
      // Store results for display
      setResultsData(result.table_data);
      setShowResults(true);
      
      // Also create download link from base64
      const byteCharacters = atob(result.spreadsheet_base64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { 
        type: data.export_format === 'xlsx' 
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
          : 'text/csv' 
      });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      return result;
    }
  });

  const addInput = () => {
    const newId = Date.now().toString();
    setInputs([...inputs, { id: newId, type: 'text', content: '' }]);
  };

  const removeInput = (id: string) => {
    setInputs(inputs.filter(input => input.id !== id));
  };

  const updateInput = (id: string, updates: Partial<BatchInput>) => {
    setInputs(inputs.map(input => 
      input.id === id ? { ...input, ...updates } : input
    ));
  };

  const handleFileSelect = (id: string, files: FileList | null) => {
    if (files && files[0]) {
      updateInput(id, { 
        file: files[0], 
        filename: files[0].name,
        content: files[0].name 
      });
    }
  };

  const handleFolderSelect = (id: string, files: FileList | null) => {
    if (files && files.length > 0) {
      // Filter for supported file types
      const supportedFiles = Array.from(files).filter(file => 
        file.name.endsWith('.txt') || file.name.endsWith('.docx')
      );
      
      if (supportedFiles.length > 0) {
        updateInput(id, { 
          files: supportedFiles,
          filenames: supportedFiles.map(f => f.name),
          content: `${supportedFiles.length} files selected`
        });
      }
    }
  };

  const handleAnalyze = () => {
    if (!selectedSchemaId) return;
    
    // Separate inputs by type
    const fileInputs = inputs.filter(input => input.type === 'file' && input.file);
    const folderInputs = inputs.filter(input => input.type === 'folder' && input.files && input.files.length > 0);
    const textInputs = inputs.filter(input => input.type === 'text' && input.content.trim());
    const urlInputs = inputs.filter(input => input.type === 'url' && input.content.trim());

    // Always use the unified endpoint that handles all input types
    const formData = new FormData();
    
    // Add individual files
    fileInputs.forEach(input => {
      formData.append('files', input.file!);
    });
    
    // Add files from folders
    folderInputs.forEach(input => {
      input.files!.forEach(file => {
        formData.append('files', file);
      });
    });
    
    // Add texts and URLs as JSON arrays
    formData.append('texts', JSON.stringify(textInputs.map(input => input.content)));
    formData.append('urls', JSON.stringify(urlInputs.map(input => input.content)));
    formData.append('schema_template_id', selectedSchemaId);
    formData.append('export_format', exportFormat);

    // Use the unified mutation
    batchAllMutation.mutate(formData);
  };

  // Unified mutation for all input types
  const batchAllMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await fetch('/api/batch/analyze-all-with-preview', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Batch analysis failed');
      }

      const result = await response.json();
      
      // Store results for display
      setResultsData(result.table_data);
      setShowResults(true);
      
      // Also create download link from base64
      const byteCharacters = atob(result.spreadsheet_base64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { 
        type: formData.get('export_format') === 'xlsx' 
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'text/csv'
      });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }
  });

  const isProcessing = batchFilesMutation.isPending || batchMixedMutation.isPending || batchAllMutation.isPending;
  const isSuccess = batchFilesMutation.isSuccess || batchMixedMutation.isSuccess || batchAllMutation.isSuccess;
  const isError = batchFilesMutation.isError || batchMixedMutation.isError || batchAllMutation.isError;

  const getInputIcon = (type: string) => {
    switch (type) {
      case 'text': return <Type className="h-4 w-4" />;
      case 'file': return <Upload className="h-4 w-4" />;
      case 'folder': return <FolderOpen className="h-4 w-4" />;
      case 'url': return <Link className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            Batch Document Processing
          </CardTitle>
          <CardDescription>
            Process multiple documents at once and download results as a spreadsheet. 
            You can mix text inputs, file uploads, and Google Drive links.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Batch Input Cards */}
      <div className="space-y-4">
        {inputs.map((input, index) => (
          <Card key={input.id}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Document {index + 1}</Badge>
                  <Select 
                    value={input.type} 
                    onValueChange={(value: 'text' | 'file' | 'url') => updateInput(input.id, { type: value })}
                  >
                    <SelectTrigger className="w-32 h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text">
                        <div className="flex items-center gap-2">
                          <Type className="h-3 w-3" />
                          Text
                        </div>
                      </SelectItem>
                      <SelectItem value="file">
                        <div className="flex items-center gap-2">
                          <Upload className="h-3 w-3" />
                          File
                        </div>
                      </SelectItem>
                      <SelectItem value="folder">
                        <div className="flex items-center gap-2">
                          <FolderOpen className="h-3 w-3" />
                          Folder
                        </div>
                      </SelectItem>
                      <SelectItem value="url">
                        <div className="flex items-center gap-2">
                          <Link className="h-3 w-3" />
                          Google Drive
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {inputs.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeInput(input.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {input.type === 'text' && (
                <Textarea
                  placeholder="Paste customer meeting notes here..."
                  value={input.content}
                  onChange={(e) => updateInput(input.id, { content: e.target.value })}
                  className="min-h-[120px]"
                />
              )}
              {input.type === 'file' && (
                <div className="space-y-2">
                  <input
                    ref={(el) => { fileInputRefs.current[input.id] = el; }}
                    type="file"
                    accept=".txt,.docx"
                    onChange={(e) => handleFileSelect(input.id, e.target.files)}
                    className="hidden"
                  />
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => fileInputRefs.current[input.id]?.click()}
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    {input.file ? input.filename : 'Choose file (.txt or .docx)'}
                  </Button>
                  {input.file && (
                    <div className="text-sm text-muted-foreground">
                      Selected: {input.filename}
                    </div>
                  )}
                </div>
              )}
              {input.type === 'folder' && (
                <div className="space-y-2">
                  <input
                    ref={(el) => { fileInputRefs.current[input.id] = el; }}
                    type="file"
                    accept=".txt,.docx"
                    multiple
                    webkitdirectory=""
                    onChange={(e) => handleFolderSelect(input.id, e.target.files)}
                    className="hidden"
                  />
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => fileInputRefs.current[input.id]?.click()}
                  >
                    <FolderOpen className="mr-2 h-4 w-4" />
                    {input.files ? `${input.files.length} files selected` : 'Choose folder'}
                  </Button>
                  {input.files && input.files.length > 0 && (
                    <div className="text-sm text-muted-foreground space-y-1 max-h-32 overflow-y-auto">
                      <div>Selected files:</div>
                      {input.filenames?.map((name, idx) => (
                        <div key={idx} className="pl-4">• {name}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {input.type === 'url' && (
                <Input
                  placeholder="https://drive.google.com/file/d/..."
                  value={input.content}
                  onChange={(e) => updateInput(input.id, { content: e.target.value })}
                />
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Add More Button */}
      <Button
        variant="outline"
        className="w-full"
        onClick={addInput}
      >
        <Plus className="mr-2 h-4 w-4" />
        Add Another Document
      </Button>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Export Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">Export Format:</label>
            <Select value={exportFormat} onValueChange={(value: 'csv' | 'xlsx' | 'preview') => setExportFormat(value as any)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="preview">
                  <div className="flex items-center gap-2">
                    <Table className="h-3 w-3" />
                    Preview Only
                  </div>
                </SelectItem>
                <SelectItem value="xlsx">
                  <div className="flex items-center gap-2">
                    <FileSpreadsheet className="h-3 w-3" />
                    Excel (.xlsx)
                  </div>
                </SelectItem>
                <SelectItem value="csv">
                  <div className="flex items-center gap-2">
                    <FileText className="h-3 w-3" />
                    CSV (.csv)
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          className="flex-1"
          onClick={handleAnalyze}
          disabled={!selectedSchemaId || inputs.length === 0 || isProcessing}
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Download className="mr-2 h-4 w-4" />
              Analyze & Download
            </>
          )}
        </Button>
      </div>

      {/* Status Messages */}
      {isSuccess && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Analysis complete! Your spreadsheet has been downloaded.
          </AlertDescription>
        </Alert>
      )}

      {isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Analysis failed. Please check your inputs and try again.
          </AlertDescription>
        </Alert>
      )}

      {/* Results Table */}
      {showResults && resultsData.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Table className="h-5 w-5" />
                Analysis Results
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  // Copy table as tab-separated values for Google Sheets
                  const headers = Object.keys(resultsData[0]);
                  const rows = resultsData.map(row => 
                    headers.map(header => row[header] || '').join('\t')
                  );
                  const tableText = [headers.join('\t'), ...rows].join('\n');
                  navigator.clipboard.writeText(tableText);
                  alert('Table copied! You can now paste it into Google Sheets.');
                }}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy for Google Sheets
              </Button>
            </CardTitle>
            <CardDescription>
              Click "Copy for Google Sheets" to copy the table in a format that pastes perfectly into Google Sheets
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    {Object.keys(resultsData[0]).map((header) => (
                      <th key={header} className="text-left p-2 font-medium text-sm">
                        {header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {resultsData.map((row, idx) => (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      {Object.entries(row).map(([key, value]) => (
                        <td key={key} className="p-2 text-sm">
                          {value || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BatchAnalysis;