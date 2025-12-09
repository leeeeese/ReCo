import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { ExternalLink, TrendingUp } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

type ProductCardProps = {
  image: string;
  name: string;
  price: string;
  avgPrice?: string;
  score?: number;
  reason?: string;
  site?: string;
  link?: string;
  compact?: boolean;
};

export default function ProductCard({
  image,
  name,
  price,
  avgPrice,
  score,
  reason,
  site,
  link,
  compact = false,
}: ProductCardProps) {
  return (
    <Card
      className={`overflow-hidden rounded-3xl hover:shadow-lg transition-shadow ${
        compact ? "p-3" : "p-0"
      }`}
    >
      <div className={compact ? "flex gap-3" : ""}>
        <ImageWithFallback
          src={image}
          alt={name}
          className={
            compact
              ? "w-20 h-20 rounded-2xl object-cover"
              : "w-full h-48 object-cover"
          }
        />
        <div className={compact ? "flex-1 min-w-0" : "p-5"}>
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className={`${compact ? "text-sm" : ""} truncate`}>{name}</h3>
            {score && (
              <Badge className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl shrink-0">
                {score}/100
              </Badge>
            )}
          </div>

          <div
            className={`flex items-baseline gap-2 mb-2 ${
              compact ? "text-sm" : ""
            }`}
          >
            <span className="text-emerald-600">{price}</span>
            {avgPrice && (
              <>
                <span className="text-gray-400 line-through text-sm">
                  {avgPrice}
                </span>
                <TrendingUp size={16} className="text-green-500" />
              </>
            )}
          </div>

          {site && !compact && (
            <p className="text-sm text-gray-600 mb-3">출처: {site}</p>
          )}

          {reason && !compact && (
            <div className="mb-4">
              <p className="text-xs text-gray-500 mb-1 font-medium">
                추천 이유:
              </p>
              <p className="text-sm text-gray-700 line-clamp-3 leading-relaxed">
                {reason}
              </p>
            </div>
          )}

          {link && !compact && (
            <Button
              className="w-full rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
              onClick={() => window.open(link, "_blank")}
            >
              자세히 보기
              <ExternalLink size={16} className="ml-2" />
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
