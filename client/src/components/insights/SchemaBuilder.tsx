import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Plus, X, Edit, Trash2, AlertCircle, CheckCircle, Settings } from 'lucide-react';
import { ApiService } from '@/fastapi_client';

interface CategoryDefinition {
  name: string;
  description?: string;
  value_type: 'predefined' | 'inferred';
  possible_values?: string[];
}

interface SchemaTemplate {
  template_id?: string;
  template_name: string;
  categories: CategoryDefinition[];
  is_default?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface SchemaBuilderProps {
  onSchemaSelected?: (templateId: string) => void;
  selectedSchemaId?: string;
}

const SchemaBuilder: React.FC<SchemaBuilderProps> = ({ onSchemaSelected, selectedSchemaId }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingSchemaId, setEditingSchemaId] = useState<string | null>(null);
  const [newSchema, setNewSchema] = useState<SchemaTemplate>({
    template_name: '',
    categories: []
  });
  const [editingCategory, setEditingCategory] = useState<CategoryDefinition | null>(null);
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [categoryForm, setCategoryForm] = useState<CategoryDefinition>({
    name: '',
    description: '',
    value_type: 'predefined',
    possible_values: []
  });
  const [valueInput, setValueInput] = useState('');

  const queryClient = useQueryClient();

  // Fetch schema templates
  const { data: templates, isLoading } = useQuery({
    queryKey: ['schema-templates'],
    queryFn: async () => {
      const response = await fetch('/api/schema/templates');
      if (!response.ok) {
        throw new Error('Failed to fetch templates');
      }
      return await response.json() as SchemaTemplate[];
    }
  });

  // Update schema mutation
  const updateSchemaMutation = useMutation({
    mutationFn: async ({ templateId, schema }: { templateId: string; schema: { template_name: string; categories: CategoryDefinition[] } }) => {
      const response = await fetch(`/api/schema/templates/${templateId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(schema)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to update schema');
      }
      
      return await response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schema-templates'] });
      setIsEditing(false);
      setEditingSchemaId(null);
      setNewSchema({ template_name: '', categories: [] });
    },
    onError: (error) => {
      console.error('Schema update error:', error);
    }
  });

  // Create schema mutation
  const createSchemaMutation = useMutation({
    mutationFn: async (schema: { template_name: string; categories: CategoryDefinition[] }) => {
      console.log('Creating schema:', schema);
      
      const response = await fetch('/api/schema/templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(schema)
      });
      
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Schema creation error:', errorData);
        throw new Error(errorData.detail || 'Failed to create schema');
      }
      
      const result = await response.json();
      console.log('Schema created successfully:', result);
      return result;
    },
    onSuccess: (data) => {
      console.log('Schema creation succeeded:', data);
      queryClient.invalidateQueries({ queryKey: ['schema-templates'] });
      setIsCreating(false);
      setNewSchema({ template_name: '', categories: [] });
    },
    onError: (error) => {
      console.error('Schema creation mutation error:', error);
    }
  });

  const handleAddCategory = () => {
    setEditingCategory(null);
    setShowCategoryForm(true);
    setCategoryForm({
      name: '',
      description: '',
      value_type: 'predefined',
      possible_values: []
    });
  };

  const handleSaveCategory = () => {
    if (!categoryForm.name.trim()) return;

    const category: CategoryDefinition = {
      ...categoryForm,
      possible_values: categoryForm.value_type === 'predefined' ? categoryForm.possible_values : undefined
    };

    if (editingCategory) {
      // Update existing category
      const updatedCategories = newSchema.categories.map(cat => 
        cat.name === editingCategory.name ? category : cat
      );
      setNewSchema({ ...newSchema, categories: updatedCategories });
    } else {
      // Add new category
      setNewSchema({ 
        ...newSchema, 
        categories: [...newSchema.categories, category] 
      });
    }

    setEditingCategory(null);
    setShowCategoryForm(false);
    setCategoryForm({
      name: '',
      description: '',
      value_type: 'predefined',
      possible_values: []
    });
  };

  const handleAddValue = () => {
    if (!valueInput.trim()) return;
    
    setCategoryForm({
      ...categoryForm,
      possible_values: [...(categoryForm.possible_values || []), valueInput.trim()]
    });
    setValueInput('');
  };

  const handleRemoveValue = (index: number) => {
    const updatedValues = categoryForm.possible_values?.filter((_, i) => i !== index) || [];
    setCategoryForm({ ...categoryForm, possible_values: updatedValues });
  };

  const handleDeleteCategory = (categoryName: string) => {
    setNewSchema({
      ...newSchema,
      categories: newSchema.categories.filter(cat => cat.name !== categoryName)
    });
  };

  const handleCreateSchema = () => {
    console.log('handleCreateSchema called');
    console.log('newSchema:', newSchema);
    console.log('template_name length:', newSchema.template_name.trim().length);
    console.log('categories length:', newSchema.categories.length);
    
    if (!newSchema.template_name.trim() || newSchema.categories.length === 0) {
      console.log('Validation failed - empty name or no categories');
      return;
    }
    
    console.log('Starting schema creation mutation');
    createSchemaMutation.mutate({
      template_name: newSchema.template_name,
      categories: newSchema.categories
    });
  };

  const handleEditSchema = (e: React.MouseEvent, template: SchemaTemplate) => {
    e.stopPropagation(); // Prevent card selection
    setEditingSchemaId(template.template_id!);
    setNewSchema({
      template_name: template.template_name,
      categories: [...template.categories]
    });
    setIsEditing(true);
    setIsCreating(true); // Open the dialog
  };

  const handleUpdateSchema = () => {
    if (!newSchema.template_name.trim() || newSchema.categories.length === 0) {
      return;
    }
    if (editingSchemaId) {
      updateSchemaMutation.mutate({ 
        templateId: editingSchemaId, 
        schema: newSchema 
      });
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditingSchemaId(null);
    setNewSchema({ template_name: '', categories: [] });
  };

  return (
    <div className="space-y-6">
      {/* Schema Templates List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Schema Templates</h3>
          <Dialog open={isCreating} onOpenChange={setIsCreating}>
            <DialogTrigger asChild>
              <Button onClick={() => setIsCreating(true)}>
                <Plus className="h-4 w-4 mr-2" />
                New Schema
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{isEditing ? 'Edit Schema Template' : 'Create New Schema Template'}</DialogTitle>
                <DialogDescription>
                  Define categories and values for extracting insights from customer notes
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-6">
                {/* Schema Name */}
                <div>
                  <Label htmlFor="schema-name">Template Name</Label>
                  <Input
                    id="schema-name"
                    placeholder="e.g., Customer Pain Points"
                    value={newSchema.template_name}
                    onChange={(e) => setNewSchema({ ...newSchema, template_name: e.target.value })}
                  />
                </div>

                {/* Categories List */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <Label>Categories ({newSchema.categories.length})</Label>
                    <Button size="sm" onClick={handleAddCategory}>
                      <Plus className="h-4 w-4 mr-1" />
                      Add Category
                    </Button>
                  </div>

                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {newSchema.categories.map((category, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{category.name}</span>
                            <Badge variant={category.value_type === 'predefined' ? 'default' : 'secondary'}>
                              {category.value_type}
                            </Badge>
                          </div>
                          {category.description && (
                            <p className="text-sm text-gray-600 mt-1">{category.description}</p>
                          )}
                          {category.possible_values && category.possible_values.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {category.possible_values.map((value, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {value}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setEditingCategory(category);
                              setShowCategoryForm(true);
                              setCategoryForm({ ...category });
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteCategory(category.name)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Category Form */}
                {(editingCategory !== null || showCategoryForm) && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">
                        {editingCategory ? 'Edit Category' : 'New Category'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <Label>Category Name</Label>
                        <Input
                          placeholder="e.g., Product, Industry, Use Case"
                          value={categoryForm.name}
                          onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                        />
                      </div>

                      <div>
                        <Label>Description (Optional)</Label>
                        <Textarea
                          placeholder="Help the AI understand what to look for in this category"
                          value={categoryForm.description}
                          onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                          rows={2}
                        />
                      </div>

                      <div>
                        <Label>Value Type</Label>
                        <Select
                          value={categoryForm.value_type}
                          onValueChange={(value: 'predefined' | 'inferred') => 
                            setCategoryForm({ ...categoryForm, value_type: value, possible_values: value === 'inferred' ? [] : categoryForm.possible_values })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="predefined">Predefined Values</SelectItem>
                            <SelectItem value="inferred">AI Inferred</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {categoryForm.value_type === 'predefined' && (
                        <div>
                          <Label>Possible Values</Label>
                          <div className="flex gap-2 mb-2">
                            <Input
                              placeholder="Enter a value"
                              value={valueInput}
                              onChange={(e) => setValueInput(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && handleAddValue()}
                            />
                            <Button onClick={handleAddValue} disabled={!valueInput.trim()}>
                              Add
                            </Button>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {categoryForm.possible_values?.map((value, i) => (
                              <Badge key={i} variant="outline" className="cursor-pointer">
                                {value}
                                <X
                                  className="h-3 w-3 ml-1"
                                  onClick={() => handleRemoveValue(i)}
                                />
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex gap-2">
                        <Button onClick={handleSaveCategory} disabled={!categoryForm.name.trim()}>
                          <CheckCircle className="h-4 w-4 mr-2" />
                          {editingCategory ? 'Update' : 'Add'} Category
                        </Button>
                        <Button variant="outline" onClick={() => {
                          setEditingCategory(null);
                          setShowCategoryForm(false);
                          setCategoryForm({
                            name: '',
                            description: '',
                            value_type: 'predefined',
                            possible_values: []
                          });
                        }}>
                          Cancel
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Create Schema Button */}
                <div className="flex justify-end gap-2 pt-4 border-t">
                  <Button variant="outline" onClick={() => {
                    if (isEditing) {
                      handleCancelEdit();
                    }
                    setIsCreating(false);
                  }}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={isEditing ? handleUpdateSchema : handleCreateSchema}
                    disabled={!newSchema.template_name.trim() || newSchema.categories.length === 0 || 
                      (isEditing ? updateSchemaMutation.isPending : createSchemaMutation.isPending)}
                  >
                    {isEditing 
                      ? (updateSchemaMutation.isPending ? 'Updating...' : 'Update Schema')
                      : (createSchemaMutation.isPending ? 'Creating...' : 'Create Schema')
                    }
                  </Button>
                </div>

                {createSchemaMutation.isError && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Failed to create schema. Please try again.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {isLoading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-4">
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates?.map((template) => (
              <Card 
                key={template.template_id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  selectedSchemaId === template.template_id ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => onSchemaSelected?.(template.template_id!)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold">{template.template_name}</h4>
                    <div className="flex items-center gap-2">
                      {template.is_default && (
                        <Badge variant="secondary" className="text-xs">Default</Badge>
                      )}
                      {!template.is_default && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => handleEditSchema(e, template)}
                          className="h-6 w-6 p-0"
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    {template.categories.length} categories
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {template.categories.map((category, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {category.name}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SchemaBuilder;