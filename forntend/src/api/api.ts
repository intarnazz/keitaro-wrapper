/**
 * Глобальный модуль API фронтенда.
 *
 * Единственная точка входа к данным: компоненты импортируют отсюда модели и сервисы,
 * а не ходят в сеть сами. Каждая модель описывает себя классом (тип берётся из него),
 * `DefaultX` возвращает её значения по умолчанию.
 */
import campaigns from './domains/campaign/campaign.service'
import directory from './domains/directory/directory.model'

export { campaigns, directory }
export { Campaign } from './domains/campaign/campaign.model'
export { CampaignForm } from './domains/campaign/campaign.form'
export { CreatedCampaign } from './domains/campaign/created-campaign.model'
export { Stream } from './domains/stream/stream.model'
export { StreamOffer } from './domains/stream/stream-offer.model'
export { Offer } from './domains/offer/offer.model'
export { OfferSearch } from './domains/offer/offer.search'
export { DirectoryItem } from './domains/directory/directory.model'
export { ApiError } from './web_services/api-error'
