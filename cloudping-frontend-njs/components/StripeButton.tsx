'use client';
// components/StripeButton.tsx
import { Heart } from 'lucide-react';

const STRIPE_CHECKOUT_URL = "https://donate.stripe.com/9AQdSj3Mh82h7a8000"; // Replace with your actual Stripe checkout URL

export default function StripeButton() {
  return (
    <a
      href={STRIPE_CHECKOUT_URL}
      target="_blank"
      rel="noopener noreferrer"
      className="bg-gradient-to-b from-blue-600 to-blue-700 border border-blue-500 rounded px-3 py-1 text-white text-sm hover:from-blue-500 hover:to-blue-600 transition-all flex items-center gap-1.5"
    >
      <Heart size={14} className="text-pink-300" />
      <span>Support this project</span>
    </a>
  );
}