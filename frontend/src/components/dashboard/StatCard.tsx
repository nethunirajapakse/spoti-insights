interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon?: React.ReactNode;
  image?: string;
  trend?: string;
}

export const StatCard = ({ label, value, subValue, icon, image, trend }: StatCardProps) => (
  <div className="glass-card p-6 rounded-2xl flex flex-col justify-between h-40">
    <p className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">{label}</p>
    <div className="flex items-center gap-4 mt-2">
      {image && <img src={image} className="w-14 h-14 rounded-full object-cover border-2 border-primary/20" alt="" />}
      <div>
        <p className="text-2xl font-bold text-white leading-tight">{value}</p>
        {subValue && <p className="text-primary text-xs font-bold">{subValue}</p>}
        {trend && (
          <div className="flex items-center gap-1 text-primary mt-1">
             <span className="text-[10px] font-bold">{trend}</span>
          </div>
        )}
      </div>
    </div>
  </div>
)
