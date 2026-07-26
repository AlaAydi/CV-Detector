import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AnalysisResult,
  AnalysisSummary,
  DashboardStats,
  Resume,
} from '../../models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  uploadResume(file: File): Observable<Resume> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<Resume>(`${this.baseUrl}/api/resumes/upload`, formData);
  }

  analyze(resumeId: number, jobDescription: string): Observable<AnalysisResult> {
    return this.http.post<AnalysisResult>(`${this.baseUrl}/api/analysis/match`, {
      resume_id: resumeId,
      job_description: jobDescription,
    });
  }

  getHistory(): Observable<AnalysisSummary[]> {
    return this.http.get<AnalysisSummary[]>(`${this.baseUrl}/api/analysis/history`);
  }

  getAnalysis(id: number): Observable<AnalysisResult> {
    return this.http.get<AnalysisResult>(`${this.baseUrl}/api/analysis/${id}`);
  }

  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.baseUrl}/api/dashboard/stats`);
  }

  downloadOptimized(analysisId: number, format: 'pdf' | 'docx'): string {
    return `${this.baseUrl}/api/analysis/${analysisId}/download/${format}`;
  }
}
