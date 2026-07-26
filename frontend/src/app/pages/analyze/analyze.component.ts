import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { ApiService } from '../../core/services/api.service';
import { AnalysisResult, Resume } from '../../models';

@Component({
  selector: 'app-analyze',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    MatChipsModule,
    MatDividerModule,
  ],
  templateUrl: './analyze.component.html',
  styleUrl: './analyze.component.scss',
})
export class AnalyzeComponent {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);

  selectedFile: File | null = null;
  resume: Resume | null = null;
  result: AnalysisResult | null = null;
  error = '';
  loading = false;
  step: 'upload' | 'analyze' | 'result' = 'upload';

  form = this.fb.group({
    jobDescription: ['', [Validators.required, Validators.minLength(20)]],
  });

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
    this.error = '';
  }

  uploadCv(): void {
    if (!this.selectedFile) {
      this.error = 'Sélectionnez un fichier PDF ou DOCX.';
      return;
    }

    this.loading = true;
    this.api.uploadResume(this.selectedFile).subscribe({
      next: (resume) => {
        this.resume = resume;
        this.step = 'analyze';
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail ?? 'Erreur lors de l\'upload du CV.';
      },
    });
  }

  runAnalysis(): void {
    if (!this.resume || this.form.invalid) return;

    this.loading = true;
    this.error = '';
    this.api.analyze(this.resume.id, this.form.value.jobDescription!).subscribe({
      next: (result) => {
        this.result = result;
        this.step = 'result';
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail ?? 'Erreur lors de l\'analyse.';
      },
    });
  }

  reset(): void {
    this.selectedFile = null;
    this.resume = null;
    this.result = null;
    this.step = 'upload';
    this.form.reset();
  }

  download(format: 'pdf' | 'docx'): void {
    if (!this.result) return;
    window.open(this.api.downloadOptimized(this.result.id, format), '_blank');
  }

  scoreColor(score: number): string {
    if (score >= 80) return 'excellent';
    if (score >= 65) return 'good';
    if (score >= 45) return 'moderate';
    return 'low';
  }
}
