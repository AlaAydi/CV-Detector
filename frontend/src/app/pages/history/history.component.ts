import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../core/services/api.service';
import { AnalysisResult, AnalysisSummary } from '../../models';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [RouterLink, MatCardModule, MatButtonModule, MatChipsModule],
  templateUrl: './history.component.html',
  styleUrl: './history.component.scss',
})
export class HistoryComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  history: AnalysisSummary[] = [];
  detail: AnalysisResult | null = null;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.api.getAnalysis(+id).subscribe({ next: (detail) => (this.detail = detail) });
    } else {
      this.api.getHistory().subscribe({ next: (history) => (this.history = history) });
    }
  }

  download(format: 'pdf' | 'docx'): void {
    if (!this.detail) return;
    window.open(this.api.downloadOptimized(this.detail.id, format), '_blank');
  }
}
