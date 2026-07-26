export interface User {
  id: number;
  nom: string;
  email: string;
}

export interface Resume {
  id: number;
  filename: string;
  texte_extrait: string;
}

export interface AnalysisResult {
  id: number;
  score: number;
  score_skills: number;
  score_keywords: number;
  score_experience: number;
  score_education: number;
  matched_skills: string[];
  missing_skills: string[];
  recommendations: string[];
  compatibility_level: string;
  optimized_text: string | null;
  resume_text: string;
  job_description: string;
  created_at?: string;
}

export interface AnalysisSummary {
  id: number;
  score: number;
  compatibility_level: string;
  matched_skills: string[];
  missing_skills: string[];
  created_at?: string;
}

export interface DashboardStats {
  total_analyses: number;
  average_score: number;
  last_analyses: AnalysisSummary[];
}
