import { Route as RootRoute } from './routes/__root'
import { Route as IndexRoute } from './routes/index'
import { Route as ToolRoute } from './routes/tool'
import { Route as ToolsRoute } from './routes/tools'
import { Route as AboutRoute } from './routes/about'
import { Route as CvesRoute } from './routes/cves'
import { Route as CveDetailRoute } from './routes/cve'
import { Route as OrganizationRoute } from './routes/organization'
import { Route as AssetsRoute } from './routes/assets'
import { Route as MissionsRoute } from './routes/missions'
import { Route as ThreatsRoute } from './routes/threats'

export const routeTree = RootRoute.addChildren([IndexRoute, ToolsRoute, AboutRoute, ToolRoute, CveDetailRoute, CvesRoute, OrganizationRoute, AssetsRoute, MissionsRoute, ThreatsRoute])