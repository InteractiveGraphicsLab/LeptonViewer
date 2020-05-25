info = imaqhwinfo('winvideo', 1);
info.SupportedFormats

%%
% Typically you want y16

inp = videoinput('winvideo', 1, 'Y16 _160x120');

%%
% Here's a 3d whatever it's called

frame = getsnapshot(inp);
[X,Y] = meshgrid(1:size(frame, 2), 1:size(frame, 1));
figure
msh = mesh(X, Y, frame);

%%
% loop over this again and again
% creating a live temperature model
for x =0:300
    frame = getsnapshot(inp);
    set(msh, "ZData", frame)
end