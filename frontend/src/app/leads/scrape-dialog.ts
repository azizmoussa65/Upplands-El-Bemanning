import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

import { ScrapeParams } from '../core/models';

@Component({
  selector: 'app-scrape-dialog',
  imports: [
    FormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSlideToggleModule
  ],
  templateUrl: './scrape-dialog.html',
  styleUrl: './scrape-dialog.scss'
})
export class ScrapeDialog {
  private ref = inject(MatDialogRef<ScrapeDialog>);
  data: { defaultIndustryCode: string } = inject(MAT_DIALOG_DATA);

  industryCode = this.data.defaultIndustryCode || '';
  query = '';
  county = 'Stockholm';
  maxCompanies = 300;
  pages: number | null = null;
  noEnrich = false;

  cancel(): void {
    this.ref.close();
  }

  launch(): void {
    const params: ScrapeParams = {
      industryCode: this.industryCode || undefined,
      query: this.query || undefined,
      county: this.county || undefined,
      pages: this.pages || undefined,
      maxCompanies: this.maxCompanies || undefined,
      noEnrich: this.noEnrich
    };
    this.ref.close(params);
  }
}
