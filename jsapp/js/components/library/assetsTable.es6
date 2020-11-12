import React from 'react';
import ReactDOM from 'react-dom';
import autoBind from 'react-autobind';
import ui from 'js/ui';
import {bem} from 'js/bem';
import {
  t,
  hasVerticalScrollbar,
  getScrollbarWidth
} from 'js/utils';
import AssetsTableRow from './assetsTableRow';
import {renderLoading} from 'js/components/modalForms/modalHelpers';

/**
 * Displays a table of assets.
 *
 * @prop {string} context - One of ASSETS_TABLE_CONTEXTS.
 * @prop {boolean} [isLoading] - To display spinner.
 * @prop {string} [emptyMessage] - To display contextual empty message when zero assets.
 * @prop {Array<object>} assets - List of assets to be displayed.
 * @prop {number} totalAssets - Number of assets on all pages.
 * @prop {Array<object>} metadata - List of available filters values.
 * @prop {string} orderColumnId - Seleceted order column id, one of ASSETS_TABLE_COLUMNS.
 * @prop {string} orderValue - Seleceted order column value.
 * @prop {columnChangeCallback} onOrderChange - Called when user selects a column for odering.
 * @prop {string} filterColumnId - Seleceted filter column, one of ASSETS_TABLE_COLUMNS.
 * @prop {string} filterValue - Seleceted filter column value.
 * @prop {columnChangeCallback} onFilterChange - Called when user selects a column for filtering.
 * @prop {number} [currentPage] - For displaying pagination.
 * @prop {number} [totalPages] - For displaying pagination.
 * @prop {switchPageCallback} [onSwitchPage] - Called when user clicks page change.
 */
export class AssetsTable extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      shouldHidePopover: false,
      isPopoverVisible: false,
      scrollbarWidth: null,
      isFullscreen: false
    };
    this.bodyRef = React.createRef();
    autoBind(this);
  }

  componentDidMount() {
    this.updateScrollbarWidth();
    window.addEventListener('resize', this.updateScrollbarWidth);
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.updateScrollbarWidth);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.isLoading !== this.props.isLoading) {
      this.updateScrollbarWidth();
    }
  }

  toggleFullscreen() {
    this.setState({isFullscreen: !this.state.isFullscreen});
  }

  updateScrollbarWidth() {
    if (
      this.bodyRef &&
      this.bodyRef.current &&
      hasVerticalScrollbar(ReactDOM.findDOMNode(this.bodyRef.current))
    ) {
      this.setState({scrollbarWidth: getScrollbarWidth()});
    } else {
      this.setState({scrollbarWidth: null});
    }
  }

  /**
   * @param {number} newPageNumber
   */
  switchPage(newPageNumber) {
    this.props.onSwitchPage(newPageNumber);
  }

  /**
   * This function is only a callback handler, as the asset reordering itself
   * should be handled by the component that is providing the assets list.
   * @param {string} columnId
   */
  onChangeOrder(columnId) {
    if (this.props.orderColumnId === columnId) {
      // clicking already selected column results in switching the order direction
      let newVal;
      if (this.props.orderValue === ORDER_DIRECTIONS.get('ascending')) {
        newVal = ORDER_DIRECTIONS.get('descending');
      } else if (this.props.orderValue === ORDER_DIRECTIONS.get('descending')) {
        newVal = ORDER_DIRECTIONS.get('ascending');
      }
      this.props.onOrderChange(this.props.orderColumnId, newVal);
    } else {
      // change column and revert order direction to default
      this.props.onOrderChange(columnId, ASSETS_TABLE_COLUMNS.get(columnId).defaultValue);
    }
  }

  /**
   * This function is only a callback handler, as the asset filtering itself
   * should be handled by the component that is providing the assets list.
   * @param {string} columnId
   * @param {string} filterValue
   */
  onChangeFilter(columnId, filterValue) {
    if (
      this.props.filterColumnId === columnId &&
      this.props.filterValue === filterValue
    ) {
      // when clicking already selected item, clear it
      this.props.onFilterChange(null, null);
    } else {
      this.props.onFilterChange(columnId, filterValue);
    }
  }

  /**
   * @param {AssetsTableColumn} columnDef - Given column definition.
   * @param {string} [option] - Currently either 'first' or 'last'.
   */
  renderHeader(columnDef, option) {
    if (columnDef.orderBy) {
      return this.renderOrderableHeader(columnDef, option);
    } else if (columnDef.filterBy) {
      return this.renderFilterableHeader(columnDef, option);
    } else {
      return (
        <bem.AssetsTableRow__column m={columnDef.id} disabled>
          {columnDef.label}
        </bem.AssetsTableRow__column>
      );
    }
  }

  onMouseLeave() {
    // force hide popover in next render cycle
    // (ui.PopoverMenu interface handles it this way)
    if (this.state.isPopoverVisible) {
      this.setState({shouldHidePopover: true});
    }
  }

  onPopoverSetVisible() {
    this.setState({isPopoverVisible: true});
  }

  renderFilterableHeader(columnDef) {
    let options = [];
    if (this.props.metadata[columnDef.filterByMetadataName]) {
      options = this.props.metadata[columnDef.filterByMetadataName];
    }

    if (options.length === 0) {
      return (
        <bem.AssetsTableRow__column m={columnDef.id} disabled>
          {columnDef.label}
        </bem.AssetsTableRow__column>
      );
    }

    // empty icon to take up space in column
    let icon = (<i className='k-icon k-icon-filter-arrows'/>);
    if (this.props.filterColumnId === columnDef.id) {
      icon = (<i className='k-icon k-icon-check'/>);
    }

    return (
      <bem.AssetsTableRow__column m={columnDef.id}>
        <ui.PopoverMenu
          type='assets-table'
          triggerLabel={<span>{columnDef.label} {icon}</span>}
          clearPopover={this.state.shouldHidePopover}
          popoverSetVisible={this.onPopoverSetVisible}
        >
          {options.map((option, index) => {
            let optionValue;
            let optionLabel;

            if (typeof option === 'string') {
              optionValue = option;
              optionLabel = option;
            }
            if (Array.isArray(option)) {
              optionValue = option[0];
              optionLabel = option[1];
            }

            return (
              <bem.PopoverMenu__link
                onClick={this.onChangeFilter.bind(this, columnDef.id, optionValue)}
                key={`option-${index}`}
              >
                {optionLabel}
                {optionValue === this.props.filterValue &&
                  <i className='k-icon k-icon-check'/>
                }
              </bem.PopoverMenu__link>
            );
          })}
        </ui.PopoverMenu>
      </bem.AssetsTableRow__column>
    );
  }

  renderOrderableHeader(columnDef) {
    let hideIcon = false;
    let hideLabel = false;

    // for `icon-status` we don't display empty icon, because the column is
    // too narrow to display label and icon together
    if (columnDef.id === ASSETS_TABLE_COLUMNS.get('icon-status').id) {
      hideIcon = this.props.orderColumnId !== columnDef.id;
      hideLabel = this.props.orderColumnId === columnDef.id;
    }

    // empty icon to take up space in column
    let icon = (<i className='k-icon'/>);
    if (this.props.orderColumnId === columnDef.id) {
      if (this.props.orderValue === ORDER_DIRECTIONS.get('ascending')) {
        icon = (<i className='k-icon k-icon-up'/>);
      }
      if (this.props.orderValue === ORDER_DIRECTIONS.get('descending')) {
        icon = (<i className='k-icon k-icon-down'/>);
      }
    }

    const classNames = [];

    return (
      <bem.AssetsTableRow__column
        m={columnDef.id}
        onClick={this.onChangeOrder.bind(this, columnDef.id)}
        classNames={classNames}
      >
        {!hideLabel &&
          <bem.AssetsTableRow__headerLabel>{columnDef.label}</bem.AssetsTableRow__headerLabel>
        }
        {!hideIcon && icon}
      </bem.AssetsTableRow__column>
    );
  }

  /**
   * Safe: returns nothing if pagination properties are not set.
   */
  renderPagination() {
    const hasPagination = (
      typeof this.props.currentPage === 'number' &&
      typeof this.props.totalPages === 'number' &&
      typeof this.props.onSwitchPage === 'function'
    );
    const naturalCurrentPage = this.props.currentPage + 1;

    if (hasPagination) {
      return (
        <bem.AssetsTablePagination>
          <bem.AssetsTablePagination__button
            disabled={this.props.currentPage === 0}
            onClick={this.switchPage.bind(this, this.props.currentPage - 1)}
          >
            <i className='k-icon k-icon-prev'/>
            {t('Previous')}
          </bem.AssetsTablePagination__button>

          <bem.AssetsTablePagination__index>
            {/* we avoid displaying 1/0 as it doesn't make sense to humans */}
            {naturalCurrentPage}/{this.props.totalPages || 1}
          </bem.AssetsTablePagination__index>

          <bem.AssetsTablePagination__button
            disabled={naturalCurrentPage >= this.props.totalPages}
            onClick={this.switchPage.bind(this, this.props.currentPage + 1)}
          >
            {t('Next')}
            <i className='k-icon k-icon-next'/>
          </bem.AssetsTablePagination__button>
        </bem.AssetsTablePagination>
      );
    } else {
      return null;
    }
  }

  renderFooter() {
    return (
      <bem.AssetsTable__footer>
        {this.props.totalAssets !== null &&
          <span>
            {t('##count## items').replace('##count##', this.props.totalAssets)}
          </span>
        }

        {this.renderPagination()}

        {this.props.totalAssets !== null &&
          <button
            className='mdl-button'
            onClick={this.toggleFullscreen}
          >
            {t('Toggle fullscreen')}
            <i className='k-icon k-icon-expand' />
          </button>
        }
      </bem.AssetsTable__footer>
    );
  }

  render() {
    const modifiers = [this.props.context];
    if (this.state.isFullscreen) {
      modifiers.push('fullscreen');
    }

    return (
      <bem.AssetsTable m={modifiers}>
        <bem.AssetsTable__header>
          <bem.AssetsTableRow m='header'>
            {this.renderHeader(ASSETS_TABLE_COLUMNS.get('icon-status'), 'first')}
            {this.renderHeader(ASSETS_TABLE_COLUMNS.get('name'))}
            {this.renderHeader(ASSETS_TABLE_COLUMNS.get('items-count'))}
            {this.renderHeader(ASSETS_TABLE_COLUMNS.get('owner'))}
            {this.props.context === ASSETS_TABLE_CONTEXTS.get('public-collections') &&
              this.renderHeader(ASSETS_TABLE_COLUMNS.get('subscribers-count'))
            }
            {this.renderHeader(ASSETS_TABLE_COLUMNS.get('languages'))}
            {this.props.context === ASSETS_TABLE_CONTEXTS.get('public-collections') &&
              this.renderHeader(ASSETS_TABLE_COLUMNS.get('primary-sector'))
            }
            {this.renderHeader(ASSETS_TABLE_COLUMNS.get('date-modified'), 'last')}

            {this.state.scrollbarWidth !== 0 && this.state.scrollbarWidth !== null &&
              <div
                className='assets-table__scrollbar-padding'
                style={{width: `${this.state.scrollbarWidth}px`}}
              />
            }
          </bem.AssetsTableRow>
        </bem.AssetsTable__header>

        <bem.AssetsTable__body ref={this.bodyRef}>
          {this.props.isLoading &&
            renderLoading()
          }

          {!this.props.isLoading && this.props.assets.length === 0 &&
            <bem.AssetsTableRow m='empty-message'>
              {this.props.emptyMessage || t('There are no assets to display.')}
            </bem.AssetsTableRow>
          }

          {!this.props.isLoading && this.props.assets.map((asset) => {
            return (
              <AssetsTableRow
                asset={asset}
                key={asset.uid}
                context={this.props.context}
              />
            );
          })}
        </bem.AssetsTable__body>

        {this.renderFooter()}
      </bem.AssetsTable>
    );
  }
}

export const ASSETS_TABLE_CONTEXTS = new Map();
new Set([
  'my-library',
  'collection-content',
  'public-collections'
]).forEach((name) => {ASSETS_TABLE_CONTEXTS.set(name, name);});

export const ORDER_DIRECTIONS = new Map();
new Set([
  'ascending',
  'descending'
]).forEach((name) => {ORDER_DIRECTIONS.set(name, name);});

/**
 * @typedef AssetsTableColumn
 * @prop {string} label
 * @prop {string} id
 * @prop {string} [filterBy] - a backend filter property
 * @prop {string} [filterByPath] - a path to asset property that holds the data
 * @prop {string} [filterByMetadataName] - name of the metadata property that holds the values for the filter
 * @prop {string} [orderBy] - a backend order property
 * @prop {boolean} [defaultValue]
 */
export const ASSETS_TABLE_COLUMNS = new Map([
  [
    'icon-status', {
      label: t('Type'),
      id: 'icon-status',
      orderBy: 'asset_type',
      defaultValue: ORDER_DIRECTIONS.get('ascending')
    }
  ],
  [
    'date-modified', {
      label: t('Last Modified'),
      id: 'date-modified',
      orderBy: 'date_modified',
      defaultValue: ORDER_DIRECTIONS.get('descending')
    }
  ],
  [
    'name', {
      label: t('Name'),
      id: 'name',
      orderBy: 'name',
      defaultValue: ORDER_DIRECTIONS.get('ascending')
    }
  ],
  [
    'items-count', {
      label: t('Items'),
      id: 'items-count',
      // TODO: currently it is not possible to order by summary.row_count and children.count at the same time
      // so we disable this column
      orderBy: null,
      defaultValue: null
    }
  ],
  [
    'owner', {
      label: t('Owner'),
      id: 'owner',
      orderBy: 'owner__username',
      defaultValue: ORDER_DIRECTIONS.get('ascending')
    }
  ],
  [
    'subscribers-count', {
      label: t('Subscribers'),
      id: 'subscribers-count',
      orderBy: 'subscribers_count',
      defaultValue: ORDER_DIRECTIONS.get('ascending')
    }
  ],
  [
    'languages', {
      label: t('Languages'),
      id: 'languages',
      filterBy: 'summary__languages',
      filterByPath: ['summary', 'languages'],
      filterByMetadataName: 'languages'
    }
  ],
  [
    'primary-sector', {
      label: t('Primary Sector'),
      id: 'primary-sector',
      filterBy: 'settings__sector__value',
      filterByPath: ['settings', 'sector'],
      filterByMetadataName: 'sectors'
    }
  ],
]);

/**
 * @callback columnChangeCallback
 * @param {string} columnId
 * @param {string} columnValue
 */

/**
 * @callback switchPageCallback
 * @param {string} pageNumber
 */
