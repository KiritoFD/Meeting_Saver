import UIAbility from '@ohos.app.ability.UIAbility';
import AbilityConstant from '@ohos.app.ability.AbilityConstant';
import Want from '@ohos.app.ability.Want';
import window from '@ohos.window';
import { Logger } from '../utils/logger';

export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam) {
        Logger.info('Ability onCreate');
    }

    onDestroy() {
        Logger.info('Ability onDestroy');
    }

    onWindowStageCreate(windowStage: window.WindowStage) {
        Logger.info('Ability onWindowStageCreate');

        windowStage.loadContent('pages/Index', (err, data) => {
            if (err?.code) {
                Logger.error('Failed to load content', err.code.toString());
                return;
            }
            Logger.info('Succeeded in loading content');
        });
    }

    onWindowStageDestroy() {
        Logger.info('Ability onWindowStageDestroy');
    }

    onForeground() {
        Logger.info('Ability onForeground');
    }

    onBackground() {
        Logger.info('Ability onBackground');
    }
} 