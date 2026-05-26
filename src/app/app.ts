import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MerchantChatComponent } from './components/merchant-chat/merchant-chat';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, MerchantChatComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})

export class App {
  protected readonly title = signal('merchant-onboard-assist');
}
