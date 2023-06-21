var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DBC_Button_Simple = function (props) {
    const {setData, data} = props;

    function onClick() {
        setData();
    }
    return React.createElement(
        window.dash_bootstrap_components.Button,
        {
            onClick: onClick,
            color: props.color,
        },
        props.value
    );
};

// use for making dbc.Button with FontAwesome or Bootstrap icons
dagcomponentfuncs.DBC_Button = function (props) {
    const {setData, data} = props;

    function onClick() {
        setData();
    }
    let leftIcon, rightIcon;
    if (props.leftIcon) {
        leftIcon = React.createElement("i", {
            className: props.leftIcon,
        });
    }
    if (props.rightIcon) {
        rightIcon = React.createElement("i", {
            className: props.rightIcon,
        });
    }
    return React.createElement(
        window.dash_bootstrap_components.Button,
        {
            onClick,
            color: props.color,
            disabled: props.disabled,
            download: props.download,
            external_link: props.external_link,
            // change this link for your application:
            href: (props.href === undefined) ? null : 'https://finance.yahoo.com/quote/' + props.value,
            outline: props.outline,
            size: props.size,
            style: {
                margin: props.margin,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
            },
            target: props.target,
            title: props.title,
            type: props.type
        },
        leftIcon,
        props.value,
        rightIcon,
    );
};

dagcomponentfuncs.ImgThumbnail = function (props) {
    const {setData, data} = props;

    function onClick() {
        setData(props.value);
    }

    return React.createElement(
        'div',
        {
            style: {
                width     : '100%',
                height    : '100%',
                display   : 'flex',
                alignItems: 'center',
            },
        },
        React.createElement(
            'img',
            {
                onClick: onClick,
                style: {width: '100%', height: 'auto'},
                src: props.value,
            },
        )
    );
};
