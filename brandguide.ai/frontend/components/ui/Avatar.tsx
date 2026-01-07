import React from 'react';

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  fallback: string;
}

export const Avatar: React.FC<AvatarProps> = ({ src, fallback, className = '', ...props }) => {
  return (
    <div className={`relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full ${className}`} {...props}>
      {src ? (
        <img className="aspect-square h-full w-full object-cover" src={src} alt="Avatar" />
      ) : (
        <div className="flex h-full w-full items-center justify-center rounded-full bg-slate-100 text-slate-500 font-medium text-sm">
          {fallback}
        </div>
      )}
    </div>
  );
};