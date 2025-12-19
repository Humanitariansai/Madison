import React from 'react';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  className?: string;
  size?: number;
}

export const Spinner: React.FC<SpinnerProps> = ({ className = '', size = 24 }) => {
  return (
    <Loader2 
      className={`animate-spin text-primary ${className}`} 
      size={size} 
    />
  );
};