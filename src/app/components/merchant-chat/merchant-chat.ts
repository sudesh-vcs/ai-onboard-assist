import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MerchantService, ApiResponse, MerchantProfile } from '../../services/merchant.service';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  showSummary?: boolean;  // Only true when onboarding is complete
  summaryData?: any;      // The final backend payload
}

@Component({
  selector: 'app-merchant-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './merchant-chat.html',
  styleUrls: ['./merchant-chat.scss']
})
export class MerchantChatComponent implements OnInit, AfterViewChecked {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  messages: ChatMessage[] = [];
  userInput: string = '';
  isLoading: boolean = false;
  isConfirming: boolean = false;
  connectionError: boolean = false;
  debugMode: boolean = false;

  // Store profile internally but don't display until complete
  private currentProfile: MerchantProfile | null = null;

  constructor(
    private merchantService: MerchantService,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  ngOnInit() {
    this.checkBackendConnection();
    this.addSystemMessage(
      '🌟 Welcome to AI-Powered Merchant Onboarding!\n\n' +
      'I\'m your AI assistant and I\'ll help you set up your merchant profile.\n\n' +
      '💡 You can chat naturally and provide information as we go.\n' +
      'For example: "Our company is TechCorp, MID TC12345678, at 123 Main St, San Francisco, phone 555-123-4567"\n\n' +
      'Let\'s start - tell me about your organization!'
    );
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  formatMessage(content: string): SafeHtml {
    if (!content) return '';
    
    // Replace newlines with <br> tags
    let formatted = content.replace(/\n/g, '<br>');
    
    // Bold text between ** **
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    return this.sanitizer.bypassSecurityTrustHtml(formatted);
  }

  trackByFn(index: number, item: ChatMessage): number {
    return index;
  }

  scrollToBottom(): void {
    try {
      if (this.scrollContainer) {
        setTimeout(() => {
          if (this.scrollContainer) {
            this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
          }
        }, 100);
      }
    } catch(err) {
      if (this.debugMode) console.error('Scroll error:', err);
    }
  }

  checkBackendConnection() {
    this.merchantService.healthCheck().subscribe({
      next: (response) => {
        if (this.debugMode) console.log('✅ Backend connected');
        this.connectionError = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        if (this.debugMode) console.error('❌ Backend connection failed:', error);
        this.connectionError = true;
        this.addSystemMessage(
          '⚠️ Unable to connect to the backend server.\n' +
          'Please make sure the Python backend is running on http://127.0.0.1:5000'
        );
        this.cdr.detectChanges();
      }
    });
  }

  addSystemMessage(content: string) {
    this.messages = [...this.messages, {
      role: 'system',
      content: content,
      timestamp: new Date()
    }];
    this.cdr.detectChanges();
  }

  addUserMessage(content: string) {
    this.messages = [...this.messages, {
      role: 'user',
      content: content,
      timestamp: new Date()
    }];
    this.cdr.detectChanges();
  }

  addAssistantMessage(content: string, showSummary: boolean = false, summaryData?: any) {
    this.messages = [...this.messages, {
      role: 'assistant',
      content: content,
      timestamp: new Date(),
      showSummary: showSummary,
      summaryData: summaryData
    }];
    this.cdr.detectChanges();
    
    setTimeout(() => {
      this.scrollToBottom();
      this.cdr.detectChanges();
    }, 100);
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const message = this.userInput.trim();
    
    // Add user message to chat
    this.addUserMessage(message);
    this.userInput = '';
    this.isLoading = true;
    this.cdr.detectChanges();

    // Determine action based on state
    const action = this.isConfirming ? 'confirm' : 'message';

    // Run API call inside NgZone
    this.ngZone.run(() => {
      this.merchantService.sendMessage(message, action).subscribe({
        next: (response: ApiResponse) => {
          this.handleApiResponse(response);
          this.isLoading = false;
          this.cdr.detectChanges();
        },
        error: (error) => {
          if (this.debugMode) console.error('❌ API Error:', error);
          this.addAssistantMessage(
            'Sorry, I encountered an error. Please try again.'
          );
          this.isLoading = false;
          this.connectionError = true;
          this.cdr.detectChanges();
        }
      });
    });
  }

  handleApiResponse(response: ApiResponse) {
    if (!response) {
      this.addAssistantMessage('Received empty response. Please try again.');
      return;
    }

    if (response.type === 'error') {
      this.addAssistantMessage(response.message || 'An error occurred. Please try again.');
      return;
    }

    if (response.onboarding_complete) {
      // ✅ All required data collected - show summary
      this.isConfirming = false;
      this.addAssistantMessage(
        response.message,
        true,  // showSummary = true
        response.backend_payload  // Pass the final payload for display
      );
    } else if (response.type === 'success') {
      // Waiting for confirmation
      this.isConfirming = true;
      this.addAssistantMessage(response.message);
    } else {
      // Still collecting information - just show AI message
      this.isConfirming = false;
      this.addAssistantMessage(response.message);
    }
    
    this.cdr.detectChanges();
}

  onKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  resetChat() {
    this.isLoading = true;
    this.cdr.detectChanges();
    
    this.merchantService.resetSession().subscribe({
      next: () => {
        this.messages = [];
        this.currentProfile = null;
        this.isConfirming = false;
        this.isLoading = false;
        this.cdr.detectChanges();
        this.ngOnInit();
      },
      error: () => {
        this.messages = [];
        this.currentProfile = null;
        this.isConfirming = false;
        this.isLoading = false;
        this.cdr.detectChanges();
        this.ngOnInit();
      }
    });
  }

  retryConnection() {
    this.connectionError = false;
    this.cdr.detectChanges();
    this.checkBackendConnection();
  }
}