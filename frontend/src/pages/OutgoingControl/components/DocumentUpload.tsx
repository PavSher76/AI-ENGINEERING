import React, { useState, useCallback } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton
} from '@mui/material';
import { 
  CloudUpload, 
  Delete, 
  Description,
  CheckCircle,
  Error
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

interface DocumentUploadProps {
  onFileUpload: (file: File) => Promise<void>;
  onFileRemove: (file: File) => void;
  uploadedFiles: File[];
  isUploading: boolean;
  maxFileSize?: number; // в MB
  acceptedFileTypes?: string[];
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onFileUpload,
  onFileRemove,
  uploadedFiles,
  isUploading,
  maxFileSize = 10,
  acceptedFileTypes = ['.doc', '.docx', '.pdf', '.txt']
}) => {
  const [uploadError, setUploadError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploadError(null);
    
    for (const file of acceptedFiles) {
      try {
        await onFileUpload(file);
      } catch (error) {
        setUploadError(`Ошибка загрузки файла ${file.name}: ${error}`);
      }
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt']
    },
    maxSize: maxFileSize * 1024 * 1024, // конвертируем в байты
    multiple: true
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      case 'txt':
        return '📃';
      default:
        return '📄';
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Загрузка документов
      </Typography>
      
      <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover'
          }
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Отпустите файлы здесь' : 'Перетащите файлы или нажмите для выбора'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Поддерживаемые форматы: {acceptedFileTypes.join(', ')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Максимальный размер файла: {maxFileSize} MB
        </Typography>
      </Paper>

      {uploadError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {uploadError}
        </Alert>
      )}

      {isUploading && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Загрузка файлов...
          </Typography>
          <LinearProgress />
        </Box>
      )}

      {uploadedFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Загруженные файлы ({uploadedFiles.length})
          </Typography>
          <List>
            {uploadedFiles.map((file, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body1" sx={{ mr: 1 }}>
                        {getFileIcon(file)}
                      </Typography>
                      <Typography variant="body1">
                        {file.name}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary">
                      {formatFileSize(file.size)} • {file.type || 'Неизвестный тип'}
                    </Typography>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={() => onFileRemove(file)}
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Box>
  );
};

export default DocumentUpload;
