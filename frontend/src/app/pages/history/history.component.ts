import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../core/services/api.service';
import { AnalysisResult, AnalysisSummary } from '../../models';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, RouterLink, MatCardModule, MatButtonModule, MatChipsModule],
  templateUrl: './history.component.html',
  styleUrl: './history.component.scss',
})
export class HistoryComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  history: AnalysisSummary[] = [];
  detail: AnalysisResult | null = null;
  optimizedParagraphs: string[] = [];

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.api.getAnalysis(+id).subscribe({
        next: (detail) => {
          this.detail = detail;
          this.optimizedParagraphs = this.formatOptimizedText(detail.optimized_text);
        },
      });
    } else {
      this.api.getHistory().subscribe({ next: (history) => (this.history = history) });
    }
  }

  // Accepte null/undefined car le backend peut renvoyer un champ vide
  private formatOptimizedText(text: string | null | undefined): string[] {
    if (!text) return [];
    return text
      .split('•')
      .map((chunk) => chunk.trim())
      .filter((chunk) => chunk.length > 0);
  }

  compatibilityClass(level: string | null | undefined): string {
    switch ((level || '').toLowerCase()) {
      case 'high':
      case 'élevé':
        return 'badge-high';
      case 'medium':
      case 'moyen':
        return 'badge-medium';
      default:
        return 'badge-low';
    }
  }

  download(format: 'pdf' | 'docx'): void {
    if (!this.detail) return;
    window.open(this.api.downloadOptimized(this.detail.id, format), '_blank');
  }
}
