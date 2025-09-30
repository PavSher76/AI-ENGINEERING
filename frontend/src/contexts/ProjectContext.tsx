import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Project, DocumentCollection } from '../types';

interface ProjectContextType {
  currentProject: Project | null;
  projects: Project[];
  collections: DocumentCollection[];
  isLoading: boolean;
  setCurrentProject: (project: Project | null) => void;
  refreshProjects: () => Promise<void>;
  refreshCollections: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

interface ProjectProviderProps {
  children: ReactNode;
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [collections, setCollections] = useState<DocumentCollection[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refreshProjects = async () => {
    setIsLoading(true);
    try {
      // TODO: Implement API call to fetch projects
      // const response = await ProjectService.getProjects();
      // setProjects(response.data);
      
      // Mock data for now
      const mockProjects: Project[] = [
        {
          id: '1',
          name: 'Тестовый проект',
          description: 'Проект для тестирования системы',
          projectCode: 'TEST-001',
          status: 'active',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ];
      setProjects(mockProjects);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshCollections = async () => {
    if (!currentProject) return;
    
    setIsLoading(true);
    try {
      // TODO: Implement API call to fetch collections
      // const response = await RAGService.getCollections(currentProject.id);
      // setCollections(response.data);
      
      // Mock data for now
      const mockCollections: DocumentCollection[] = [
        {
          id: '1',
          name: 'Нормативные документы',
          description: 'Коллекция нормативно-технической документации',
          collectionType: 'normative',
          projectId: currentProject.id,
          documentsCount: 15,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: '2',
          name: 'Документы чата',
          description: 'Коллекция документов для чата с ИИ',
          collectionType: 'chat',
          projectId: currentProject.id,
          documentsCount: 8,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: '3',
          name: 'Исходные данные проекта',
          description: 'Коллекция исходных данных для проектирования',
          collectionType: 'input_data',
          projectId: currentProject.id,
          documentsCount: 12,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: '4',
          name: 'Документы проекта',
          description: 'Коллекция проектной документации',
          collectionType: 'project',
          projectId: currentProject.id,
          documentsCount: 25,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: '5',
          name: 'Архив и объекты аналоги',
          description: 'Коллекция архивных документов и объектов-аналогов',
          collectionType: 'archive',
          projectId: currentProject.id,
          documentsCount: 30,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ];
      setCollections(mockCollections);
    } catch (error) {
      console.error('Error fetching collections:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  useEffect(() => {
    if (currentProject) {
      refreshCollections();
    }
  }, [currentProject]);

  const value: ProjectContextType = {
    currentProject,
    projects,
    collections,
    isLoading,
    setCurrentProject,
    refreshProjects,
    refreshCollections,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = (): ProjectContextType => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};
