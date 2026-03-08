import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { BookOpen, Upload, FileText, Trash2, Plus } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

export default function KnowledgeBase() {
  const [knowledge, setKnowledge] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newKnowledge, setNewKnowledge] = useState({
    title: '',
    content: '',
    category: 'general'
  });

  useEffect(() => {
    loadKnowledge();
  }, []);

  const loadKnowledge = async () => {
    try {
      const response = await api.get('/knowledge/');
      setKnowledge(response.data);
    } catch (error) {
      toast.error('Failed to load knowledge base');
      console.error('Load knowledge error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddKnowledge = async (e) => {
    e.preventDefault();
    try {
      await api.post('/knowledge/', newKnowledge);
      toast.success('Knowledge added successfully');
      setIsAddOpen(false);
      setNewKnowledge({ title: '', content: '', category: 'general' });
      loadKnowledge();
    } catch (error) {
      toast.error('Failed to add knowledge');
      console.error('Add knowledge error:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name);
    formData.append('category', 'general');

    try {
      await api.post('/knowledge/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('File uploaded successfully');
      loadKnowledge();
    } catch (error) {
      toast.error('Failed to upload file');
      console.error('Upload file error:', error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this knowledge item?')) return;
    
    try {
      await api.delete(`/knowledge/${id}/`);
      toast.success('Knowledge deleted successfully');
      loadKnowledge();
    } catch (error) {
      toast.error('Failed to delete knowledge');
      console.error('Delete knowledge error:', error);
    }
  };

  const categoryColors = {
    general: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100',
    product: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100',
    faq: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
    policy: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100',
    sop: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
  };

  return (
    <div className="space-y-6" data-testid="knowledge-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">Knowledge Base</h1>
          <p className="text-muted-foreground">Train your AI with business knowledge and documentation</p>
        </div>
        <div className="flex gap-2">
          <label htmlFor="file-upload">
            <Button variant="outline" asChild>
              <span>
                <Upload className="h-4 w-4 mr-2" />
                Upload File
              </span>
            </Button>
          </label>
          <input
            id="file-upload"
            type="file"
            accept=".txt,.pdf,.doc,.docx"
            onChange={handleFileUpload}
            className="hidden"
            data-testid="file-upload-input"
          />
          
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button data-testid="add-knowledge-button">
                <Plus className="h-4 w-4 mr-2" />
                Add Knowledge
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Knowledge</DialogTitle>
                <DialogDescription>Add new information to train your AI assistant</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddKnowledge}>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Title</Label>
                    <Input
                      id="title"
                      value={newKnowledge.title}
                      onChange={(e) => setNewKnowledge({ ...newKnowledge, title: e.target.value })}
                      required
                      placeholder="Product Information"
                      data-testid="knowledge-title-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="category">Category</Label>
                    <Select value={newKnowledge.category} onValueChange={(value) => setNewKnowledge({ ...newKnowledge, category: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="general">General</SelectItem>
                        <SelectItem value="product">Product</SelectItem>
                        <SelectItem value="faq">FAQ</SelectItem>
                        <SelectItem value="policy">Policy</SelectItem>
                        <SelectItem value="sop">SOP</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="content">Content</Label>
                    <Textarea
                      id="content"
                      value={newKnowledge.content}
                      onChange={(e) => setNewKnowledge({ ...newKnowledge, content: e.target.value })}
                      required
                      rows={8}
                      placeholder="Enter detailed information here..."
                      data-testid="knowledge-content-input"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit" data-testid="save-knowledge-button">Save Knowledge</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Knowledge List */}
      <div className="grid grid-cols-1 gap-4">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : knowledge.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <BookOpen className="h-16 w-16 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">No knowledge items found</p>
              <Button onClick={() => setIsAddOpen(true)}>Add Your First Knowledge Item</Button>
            </CardContent>
          </Card>
        ) : (
          knowledge.map((item) => (
            <Card key={item.id} className="hover:shadow-md transition-all duration-200" data-testid="knowledge-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-5 w-5 text-primary" />
                      <CardTitle className="text-lg">{item.title}</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${categoryColors[item.category] || categoryColors.general}`}>
                        {item.category.toUpperCase()}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Added {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(item.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {item.content}
                </p>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}