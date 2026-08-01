import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';

import { ApiService } from '../core/api.service';
import { Campaign } from '../core/models';

@Component({
  selector: 'app-campaign-detail',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatChipsModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './campaign-detail.html',
  styleUrl: './campaign-detail.scss'
})
export class CampaignDetail {
  private route = inject(ActivatedRoute);
  private api = inject(ApiService);
  private snack = inject(MatSnackBar);

  campaign = signal<Campaign | null>(null);
  loading = signal(true);
  launching = signal(false);

  openRate = computed(() => {
    const c = this.campaign();
    if (!c || !c.stats.sent) return 0;
    return Math.round((c.stats.opened / c.stats.sent) * 100);
  });

  clickRate = computed(() => {
    const c = this.campaign();
    if (!c || !c.stats.sent) return 0;
    return Math.round((c.stats.clicked / c.stats.sent) * 100);
  });

  constructor() {
    this.load();
  }

  private load(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.loading.set(true);
    this.api.getCampaign(id).subscribe({
      next: (c) => {
        this.campaign.set(c);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  launch(): void {
    const c = this.campaign();
    if (!c) return;
    this.launching.set(true);
    this.api.launchCampaign(c.id).subscribe({
      next: (res) => {
        this.launching.set(false);
        this.snack.open(`${res.queued} email(s) queued`, 'OK', { duration: 4000 });
        this.load();
      },
      error: (err) => {
        this.launching.set(false);
        this.snack.open(err?.error?.error || 'Could not launch campaign', 'OK', { duration: 4000 });
      }
    });
  }
}
