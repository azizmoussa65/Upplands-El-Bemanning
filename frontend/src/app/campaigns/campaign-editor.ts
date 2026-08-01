import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';

import { ApiService } from '../core/api.service';
import { LEAD_STATUS_LABELS, LeadStatus } from '../core/models';

@Component({
  selector: 'app-campaign-editor',
  imports: [
    FormsModule,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule
  ],
  templateUrl: './campaign-editor.html',
  styleUrl: './campaign-editor.scss'
})
export class CampaignEditor {
  private api = inject(ApiService);
  private router = inject(Router);
  private snack = inject(MatSnackBar);

  readonly statusLabels = LEAD_STATUS_LABELS;
  readonly statuses = Object.keys(LEAD_STATUS_LABELS) as LeadStatus[];

  counties = signal<string[]>([]);
  recipientCount = signal<number | null>(null);
  saving = signal(false);

  name = '';
  subject = '';
  body = 'Hi {{name}},\n\nWe help electrical companies like {{company}} find qualified electricians fast...\n\nBest,\n';
  county = '';
  status = '';
  search = '';
  followUps: number[] = [3, 7];

  constructor() {
    this.api.getCounties().subscribe((counties) => this.counties.set(counties));
    this.previewRecipients();
  }

  previewRecipients(): void {
    this.api
      .previewRecipients({ county: this.county || undefined, status: this.status || undefined, search: this.search || undefined })
      .subscribe((res) => this.recipientCount.set(res.count));
  }

  addFollowUp(): void {
    const last = this.followUps[this.followUps.length - 1] ?? 3;
    this.followUps.push(last + 4);
  }

  removeFollowUp(index: number): void {
    this.followUps.splice(index, 1);
  }

  save(): void {
    if (!this.name || !this.subject || !this.body) {
      this.snack.open('Name, subject and body are required', 'OK', { duration: 4000 });
      return;
    }
    this.saving.set(true);
    this.api
      .createCampaign({
        name: this.name,
        subject: this.subject,
        body: this.body,
        followUpCadence: this.followUps.filter((d) => d > 0).map((afterDays) => ({ afterDays })),
        recipientFilter: { county: this.county || undefined, status: this.status || undefined, search: this.search || undefined }
      })
      .subscribe({
        next: (campaign) => {
          this.saving.set(false);
          this.router.navigate(['/campaigns', campaign.id]);
        },
        error: (err) => {
          this.saving.set(false);
          this.snack.open(err?.error?.error || 'Could not create campaign', 'OK', { duration: 4000 });
        }
      });
  }
}
