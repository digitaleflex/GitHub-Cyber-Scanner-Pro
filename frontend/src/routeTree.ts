import { Route as RootRoute } from './routes/__root'
import { Route as IndexRoute } from './routes/index'
import { Route as NewsRoute } from './routes/news'
import { Route as ReportsRoute } from './routes/reports'

export const routeTree = RootRoute.addChildren([IndexRoute, NewsRoute, ReportsRoute])
