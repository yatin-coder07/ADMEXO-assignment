import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

export default function ThankYou() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center">
      <div className="bg-card border border-border p-8 rounded-2xl shadow-xl max-w-md w-full">
        <div className="flex justify-center mb-6">
          <CheckCircle2 className="w-16 h-16 text-accent" />
        </div>
        <h1 className="text-3xl font-bold mb-4">Thank You!</h1>
        <p className="text-gray-400 mb-8">
          Your interest has been recorded. We will be in touch with you shortly.
        </p>
        <Link 
          href="/"
          className="inline-flex items-center justify-center px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg font-medium transition-colors w-full"
        >
          Return to Homepage
        </Link>
      </div>
    </div>
  );
}
